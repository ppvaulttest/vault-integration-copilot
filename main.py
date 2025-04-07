import streamlit as st
import openai
import os
from dotenv import load_dotenv
import json
from validator import validate_json

# Load .env for OpenAI API Key
load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Page Title
st.title("Vault v3 Co-Pilot")
st.subheader("Test Vault Integration. Just describe your goal.")

# Text Input
instruction = st.text_input("What do you want to do with Vault v3?")

# AI Fixer Function
def fix_api_error(original_instruction, error_msg):
    follow_up_prompt = f"""
The request you generated failed with this Vault API error: "{error_msg}"

Please revise the request and return a corrected JSON payload only.

Original instruction: "{original_instruction}"
"""
    client = openai.OpenAI()
    follow_up_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": follow_up_prompt}],
        temperature=0.2,
    )
    return follow_up_response.choices[0].message.content

def call_paypal_api(parsed_json):
    import requests
    
    # PayPal sandbox API endpoint
    url = "https://api-m.sandbox.paypal.com/v3/vault/payment-tokens"
    
    # Get sandbox access token from environment variable
    access_token = os.getenv("PAYPAL_SANDBOX_ACCESS_TOKEN")
    if not access_token:
        return {"error": "PayPal sandbox access token not configured"}
        
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.post(url, json=parsed_json, headers=headers)
        return response.json()
    except Exception as e:
        return {"error": f"API call failed: {str(e)}"}

# Button Action
if st.button("Generate Request") and instruction:
    with st.spinner("Thinking..."):
        try:
            # OpenAI prompt
            prompt = f"""
You are an API assistant for PayPal's **Vault v3 API** SANDBOX environment ONLY.
When the user gives an instruction, generate a valid request using the sandbox endpoint: https://api-m.sandbox.paypal.com/v3/vault/payment-tokens

The request must include:
1. Sandbox endpoint
2. Headers with:
   - Content-Type: application/json
   - Authorization: Bearer <sandbox_access_token>
3. Correct v3 format with payment_source.card structure

Example format:
{{
  "payment_source": {{
    "card": {{
      "number": "4111111111111111",
      "expiry": "2025-12",
      "security_code": "123",
      "name": "John Doe"
    }}
  }}
}}

Instruction: "{instruction}"

Return:
- Endpoint (/v3/vault/payment-tokens)
- Method (POST)
- Headers
- JSON Body (using the format above)
"""
            # OpenAI Call
            # client already initialized above
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            # Save AI output
            ai_output = response.choices[0].message.content
            st.subheader("AI-Generated Vault Request")
            st.code(ai_output)

            # Parse JSON
            try:
                # Find the JSON block between the last occurrence of '{' and the last '}'
                start_idx = ai_output.find('{\n  "payment_source"')
                end_idx = ai_output.rfind('}') + 1
                if start_idx == -1:
                    raise ValueError("No valid JSON found in response")
                json_block = ai_output[start_idx:end_idx]
                parsed_json = json.loads(json_block)
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON: {e}")
                st.stop()

            # Validate JSON
            st.subheader("JSON Validation Result")
            result = validate_json(parsed_json)
            if "✅" in result:
                st.success(result)
            else:
                st.error(result)

            # Simulate Vault API Call
            st.subheader("Simulated Vault API Response")
            api_response = call_paypal_api(parsed_json)

            if "error" in api_response:
                st.error(f"API Error: {api_response['error']}")
                # AI Suggested Fix
                st.subheader("AI-Suggested Fix")
                fixed = fix_api_error(instruction, api_response["error"])
                st.code(fixed, language="json")
            else:
                st.success("API Call Successful!")
                st.json(api_response)

        except Exception as e:
            st.warning("Something went wrong during processing.")
            st.text(str(e))
