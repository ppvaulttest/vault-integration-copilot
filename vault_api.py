import os
import requests

def get_paypal_access_token():
    client_id = os.getenv("PAYPAL_CLIENT_ID")
    client_secret = os.getenv("PAYPAL_CLIENT_SECRET")

    token_url = "https://api.sandbox.paypal.com/v1/oauth2/token"
    headers = {"Accept": "application/json", "Accept-Language": "en_US"}
    data = {"grant_type": "client_credentials"}

    response = requests.post(
        token_url,
        headers=headers,
        data=data,
        auth=(client_id, client_secret)
    )

    response.raise_for_status()
    return response.json()["access_token"]

def vault_card_in_paypal(json_body):
    access_token = get_paypal_access_token()

    vault_url = "https://api.sandbox.paypal.com/v3/vault/payment-tokens"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        vault_url,
        headers=headers,
        json=json_body
    )

    return response.status_code, response.json()
