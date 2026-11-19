import azure.functions as func
import base64, os, re, logging
import pandas as pd
import pyodbc
from datetime import date

app = func.FunctionApp()

# ── Helpers ───────────────────────────────────────────────────────────────────

MONTH_FR = {
	'jan': 1, 'fev': 2, 'mar': 3, 'avr': 4, 'mai': 5, 'juin': 6,
	'juil': 7, 'aout': 8, 'sep': 9, 'sept': 9, 'oct': 10, 'nov': 11, 'dec': 12
}
JOURS = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi']


def get_conn():
	return pyodbc.connect(
		'DRIVER={ODBC Driver 18 for SQL Server};'
		f'SERVER={os.environ["SQL_SERVER"]};'
		f'DATABASE={os.environ["SQL_DATABASE"]};'
		f'UID={os.environ["SQL_USER"]};'
		f'PWD={os.environ["SQL_PASSWORD"]}'
	)


def extract_filiere(filename: str) -> str:
	"""'EDT_ING4_CYB.xlsx' -> 'CYB'"""
	m = re.search(r'EDT_[^_]+_([^.]+)\.xlsx', filename, re.IGNORECASE)
	return m.group(1).upper() if m else 'INCONNU'


def parse_date_debut(s: str):
	"""'07-12 Sept 2026' -> date(2026, 9, 7)"""
	m = re.search(r'(\d{1,2})[-\s].*?([A-Za-z\xe9\xe8]+)\s+(\d{4})', str(s))
	if not m:
		return None
	day, mois, yr = m.group(1), m.group(2).lower()[:4], m.group(3)
	mon = MONTH_FR.get(mois)
	if not mon:
		return None
	try:
		return date(int(yr), mon, int(day))
	except ValueError:
		return None


def parse_cell(text: str):
	"""
	'TPC  Ethical hacking\nZEROUAL\nE316' -> dict
	type_seance : CM | TD | TP | CC
	groupe      : A/B/C/D/E  ou  'TOUS' (CM et CC)
	"""
	lines = [l.strip() for l in str(text).split('\n') if l.strip()]
	if not lines:
		return None
	m = re.match(r'^(CM|CC|TP|TD)\s*([A-E]?)\s+(.+)', lines[0], re.IGNORECASE)
	if not m:
		return None
	return {
		'type_seance': m.group(1).upper(),
		'groupe':      m.group(2).upper() or 'TOUS',
		'matiere':     m.group(3).strip(),
		'prof':        lines[1] if len(lines) > 1 else None,
		'salle':       lines[2] if len(lines) > 2 else None,
	}


def parse_horaire(h: str):
	m = re.search(r'(\d{1,2})[Hh](\d{2})\s*[-–]\s*(\d{1,2})[Hh](\d{2})', h)
	if not m:
		return None, None
	return (
		f'{int(m.group(1)):02d}:{m.group(2)}',
		f'{int(m.group(3)):02d}:{m.group(4)}'
	)


# ── Parseur principal ─────────────────────────────────────────────────────────

def parse_and_insert(excel_bytes: bytes, filiere: str):
	xl    = pd.read_excel(excel_bytes, sheet_name=0, header=None)
	today = date.today()
	sem   = today.isocalendar().week
	annee = today.year

	target = None
	for col in range(3, xl.shape[1], 5):
		d = parse_date_debut(xl.iloc[9, col])
		if d and d.isocalendar().week == sem and d.year == annee:
			target = col
			break

	if target is None:
		logging.warning(f"Semaine {sem}/{annee} absente du fichier {filiere}")
		return

	conn   = get_conn()
	cursor = conn.cursor()

	cursor.execute(
		'DELETE FROM seances WHERE semaine=? AND annee=? AND filiere=?',
		sem, annee, filiere
	)
	conn.commit()

	cur_jour = None
	for r in range(10, xl.shape[0]):
		j = xl.iloc[r, 1]
		if pd.notna(j) and str(j).strip().lower() in JOURS:
			cur_jour = str(j).strip().capitalize()

		h = xl.iloc[r, 2]
		if pd.isna(h) or not cur_jour:
			continue
		hd, hf = parse_horaire(str(h))
		if not hd:
			continue

		for sub in range(5):
			c = target + sub
			if c >= xl.shape[1]:
				break
			v = xl.iloc[r, c]
			if pd.isna(v):
				continue
			e = parse_cell(str(v))
			if not e:
				continue
			cursor.execute(
				'INSERT INTO seances '
				'(semaine,annee,jour,heure_debut,heure_fin,'
				'matiere,type_seance,salle,prof,filiere,groupe) '
				'VALUES (?,?,?,?,?,?,?,?,?,?,?)',
				sem, annee, cur_jour, hd, hf,
				e['matiere'], e['type_seance'],
				e['salle'], e['prof'], filiere, e['groupe']
			)

	conn.commit()
	logging.info(f"Semaine {sem}/{annee} insérée pour filière {filiere}")


# ── Azure Function ─────────────────────────────────────────────────────────────

@app.function_name('email_receiver')
@app.route(route='email', methods=['POST'])
def email_receiver(req: func.HttpRequest) -> func.HttpResponse:
	body       = req.get_json()
	attachment = body.get('attachment_content')
	filename   = body.get('attachment_name', 'EDT_ING4_INCONNU.xlsx')

	if not attachment:
		return func.HttpResponse('Pas de piece jointe', status_code=400)

	excel_bytes = base64.b64decode(attachment)

	from azure.storage.blob import BlobServiceClient
	blob = BlobServiceClient.from_connection_string(
		os.environ['AZURE_STORAGE_CONNECTION_STRING']
	)
	blob.get_container_client('excel-bruts').upload_blob(
		filename, excel_bytes, overwrite=True
	)

	filiere = extract_filiere(filename)
	parse_and_insert(excel_bytes, filiere)
	return func.HttpResponse('OK', status_code=200)






