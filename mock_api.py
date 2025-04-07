def mock_vault_api_call(payload):
    card = payload.get("payment_source", {}).get("card", {})

    if "security_code" not in card:
        return {"error": "missing_field: security_code"}

    if not card.get("number", "").startswith("4"):
        return {"error": "invalid_account_number"}

    return {"status": "success"}
