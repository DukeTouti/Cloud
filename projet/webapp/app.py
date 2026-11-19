from flask import Flask, render_template, request
import pyodbc, os
from datetime import date

app = Flask(__name__)


def get_conn():
	return pyodbc.connect(
		'DRIVER={ODBC Driver 18 for SQL Server};'
		f'SERVER={os.environ["SQL_SERVER"]};'
		f'DATABASE={os.environ["SQL_DATABASE"]};'
		f'UID={os.environ["SQL_USER"]};'
		f'PWD={os.environ["SQL_PASSWORD"]}'
	)


@app.route('/')
def index():
	return render_template('index.html')


@app.route('/edt')
def edt():
	filiere   = request.args.get('filiere',   '').upper()
	groupe_tp = request.args.get('groupe_tp', '').upper()
	groupe_td = request.args.get('groupe_td', '').upper()
	today     = date.today()
	semaine   = int(request.args.get('semaine', today.isocalendar().week))
	annee     = int(request.args.get('annee',   today.year))

	if not filiere or not groupe_tp or not groupe_td:
		return render_template('index.html', error='Remplis tous les champs.')

	conn   = get_conn()
	cursor = conn.cursor()
	cursor.execute(
		'SELECT jour, heure_debut, heure_fin, matiere, type_seance, salle, prof '
		'FROM seances '
		'WHERE filiere=? AND semaine=? AND annee=? '
		"AND (groupe='TOUS' "
		"     OR (type_seance='TP' AND groupe=?) "
		"     OR (type_seance='TD' AND groupe=?)) "
		'ORDER BY jour, heure_debut',
		filiere, semaine, annee, groupe_tp, groupe_td
	)
	seances = cursor.fetchall()

	cursor.execute(
		'SELECT DISTINCT semaine, annee FROM seances '
		'WHERE filiere=? ORDER BY annee DESC, semaine DESC',
		filiere
	)
	semaines_dispo = cursor.fetchall()

	return render_template(
		'edt.html',
		seances=seances,
		filiere=filiere,
		groupe_tp=groupe_tp,
		groupe_td=groupe_td,
		semaine=semaine,
		annee=annee,
		semaines_dispo=semaines_dispo,
	)


if __name__ == '__main__':
	app.run(debug=False, host='0.0.0.0', port=8000)
	
	
	
	
	
