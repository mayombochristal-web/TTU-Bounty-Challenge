import requests
import os
from datetime import datetime
class TTUBilling:
def __init__(self):
self.flutterwave_api_key = os.getenv("FLW_SECRET_KEY")
self.uba_merchant_account = "UBA_MERCHANT_ID" # lié à votre compte UBA
def check_quota(self, app_id):
"""Vérifie si l'application a encore des scans gratuits ou un abonnement actif."""
# Requête à la base pour connaître le statut
# Retourne True si autorisé
pass
def create_payment_link(self, app_id, plan="pro"):
"""Génère un lien de paiement Flutterwave."""
payload = {
"tx_ref": f"ttu-{app_id}-{datetime.now().timestamp()}",
"amount": "29.99",
"currency": "EUR",
"redirect_url": "https://votre-domaine.com/payment-success",
"payment_options": "card, mobilemoney",
"customer": {
"email": "client@example.com",

"name": "Client TTU"
},
"customizations": {
"title": "TTU BASTION EDR - Abonnement Pro",
"description": "Protection avancée avec dissipation illimitée"
}
}
headers = {"Authorization": f"Bearer {self.flutterwave_api_key}"}
resp = requests.post("https://api.flutterwave.com/v3/payments", json=payload,
headers=headers)
return resp.json()["data"]["link"]
def handle_webhook(self, request_data):
"""Traite la confirmation de paiement et active l'abonnement."""
# Vérifier la signature, puis mettre à jour la base
pass