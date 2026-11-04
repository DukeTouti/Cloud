import json
import requests

# Remplacez par votre URL complète de fonction incluant votre code de sécurité
url = "..."

# Données JSON à envoyer (les deux nombres pour l'addition)
payload = {"num1": 15, "num2": -20}

# Envoi de la requête POST
response = requests.post(url, json=payload)

# Affichage du résultat
print(f"Code statut : {response.status_code}")
print(f"Réponse : {response.text}")
