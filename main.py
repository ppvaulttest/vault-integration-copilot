import streamlit as st
import openai
import os
import requests
import json
from jsonschema import validate, ValidationError

# --- Streamlit Page Setup ---
st.set_page_config(page_title="Vault v3 Co-Pilot", layout="centered")
st.title("Vault v3 Co-Pilot")
st.subheader("Test Card Vaulting in PayPal Sandbox")
st.markdown("Describe your goal (e.g. 'Vault a Visa card with CVV, expiry, and billing address').")

# --- Load Secrets ---
openai.api_key = os.getenv("OPENAI_API_KEY")
paypal_client_id = os.getenv("PAYPAL_CLIENT_ID")
paypal_client_secret = os.getenv("PAYPAL_CLIENT_SECRET")

# --- JSON Schema (simplified card vaulting) ---
card_schema = {
    "type": "object",
    "properties": {
        "payment_source": {
            "type": "object",
            "properties": {
                "card": {
                    "type": "object",
                    "properties": {
                        "number": {"type": "string"},
                        "expiry": {"type": "string"},
                        "security_code": {"type": "string"},
                        "billing_address": {"type": "object"}
                    },
                    "required": ["number", "expiry", "security_code"]
                }
            },
            "required": ["card"]
        }
    },
    "required": ["payment_source"]
}

# --- Validate JSON against schema ---
def validate_json(data):
    try:
        validate(instance=data, schema=card_schema)
        return True, ""
    except ValidationError as ve:
        return False, str(ve)

# --- Get access token from PayPal Sandbox ---
def get_paypal_access_token():
    url = "https://api.sandbox.paypal.com/v1/oauth2/token"
    auth = (paypal_client_id, paypal_client_secret)
    headers = {"Accept": "application/json", "Accept-Language": "en_US"}
    data = {"grant_type": "client_credentials"}
    response = requests.post(url, headers=headers, data=data, auth=auth)
    response.raise_for_status()
    return response.json()["access_token"]

# --- Call PayPal Vault v3 API ---
def send_to_paypal(json_data):
    token = get_paypal_access_token()
    url = "https://api.sandbox.paypal.com/v3/vault/payment-tokens"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json=json_data)
    return response.status_code, response.json()

# --- UI + Prompt Flow ---
user_prompt = st.text_area("Enter your instruction")

if st.button("Generate & Validate"):
    if not user_prompt:
        st.warning("Please enter a prompt first.")
    else:
        try:
            # AI prompt to generate pure JSON
            messages = [
                {
                    "role": "system",
                    "content": "You are an assistant that only returns valid JSON for the PayPal Vault v3 API request body. Do not include any explanation or text outside the JSON object."
                },
                {
                    "role": "user",
                    "content": f"Generate a PayPal Vault v3 payment token request to: {user_prompt}"
                }
            ]
            ai_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.2
            )
            ai_output = ai_response['choices'][0]['message']['content']

            st.subheader("AI-Generated JSON")
            st.code(ai_output, language='json')

            # Try to parse and validate JSON
            try:
                parsed_json = json.loads(ai_output)
                is_valid, error_msg = validate_json(parsed_json)

                if is_valid:
                    st.success("JSON is valid according to schema.")
                    st.subheader("Sending to PayPal Sandbox...")
                    status, response = send_to_paypal(parsed_json)
                    st.success(f"Sandbox Response (Status {status})")
                    st.json(response)
                else:
                    st.error("JSON Validation Failed:")
                    st.code(error_msg)
                    if st.button("Fix JSON with AI"):
                        fix_prompt = f"The following JSON is invalid for PayPal Vault. Fix it and only return fixed JSON:\n\n{ai_output}"
                        fixed = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "Only return fixed JSON with no explanation."},
                                {"role": "user", "content": fix_prompt}
                            ],
                            temperature=0.2
                        )
                        fixed_json = fixed['choices'][0]['message']['content']
                        st.subheader("AI-Fixed JSON")
                        st.code(fixed_json, language='json')

            except json.JSONDecodeError:
                st.error("AI output is not valid JSON. Try rephrasing your prompt or click Fix JSON.")

        except Exception as e:
            st.error(f"Something went wrong: {e}")
