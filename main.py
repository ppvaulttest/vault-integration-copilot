import streamlit as st
import openai
import os
from dotenv import load_dotenv
import json
from validator import validate_json
from mock_api import mock_vault_api_call

# Load .env for OpenAI API Key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.title("Vault v3 Co-Pilot")
st.subheader("Skip the docs. Just describe your goal.")

instruction = st.text_input("What do you want to do with Vault v3?")

def fix_api_error(original_instruction, error_msg):
    follow_up_prompt = f"""
The request you generated failed with this Vault API error: "{error_msg}"

Please revise the request and return a corrected JSON payload only.

Original instruction: "{original_instruction}"
"""
    follow_up_response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": follow_up_prompt}],
        temperature=0.2,
    )
    return follow_up_response.choices[0].message.content

if st.button("Generate Request") and instruction:
    with st.spinner("Thinking..."):
        try:
            prompt = f"""
You are a developer assistant that helps generate requests for PayPal's Vault v3 API.

Always return only the raw HTTP request information in this format:

POST https://api.sandbox.paypal.com/v3/vault/payment-tokens
Headers:
Content-Type: application/json
Authorization: Bearer ACCESS-TOKEN

Request Body:
{{
  "payment_source": {{
    ...
  }}
}}

- Do NOT explain anything.
- Do NOT add any markdown headings or notes.
- Do NOT include tables or bullet points.
- Only output exactly what a developer would copy and paste into Postman or curl.

Instruction: "{instruction}"
"""

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            ai_output = response.choices[0].message.content
            ai_output = ai_output.replace("```", "").strip()
            ai_output = ai_output.replace("https://api.paypal.com", "https://api.sandbox.paypal.com")
            st.subheader("AI-Generated Vault Request")
            st.code(ai_output)

            json_block = ai_output.split("{", 1)[1]
            json_block = "{" + json_block
            parsed_json = json.loads(json_block)

            st.subheader("JSON Validation Result")
            result = validate_json(parsed_json)
            if "✅" in result:
                st.success(result)
            else:
                st.error(result)

            from mock_api import mock_vault_api_call
            st.subheader("Simulated Vault API Response")
            simulated_response = mock_vault_api_call(parsed_json)

            if "error" in simulated_response:
                st.error(f"API Error: {simulated_response['error']}")
                st.subheader("AI-Suggested Fix")
                fixed = fix_api_error(instruction, simulated_response["error"])
                st.code(fixed, language="json")
            else:
                st.success("API Call Successful!")

        except Exception as e:
            st.warning("Something went wrong during processing.")
            st.text(str(e))
