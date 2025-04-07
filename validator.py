from jsonschema import validate, ValidationError

vault_schema = {
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
                        "billing_address": {
                            "type": "object",
                            "properties": {
                                "address_line_1": {"type": "string"},
                                "admin_area_2": {"type": "string"},
                                "admin_area_1": {"type": "string"},
                                "postal_code": {"type": "string"},
                                "country_code": {"type": "string"}
                            },
                            "required": ["address_line_1", "admin_area_2", "postal_code", "country_code"]
                        }
                    },
                    "required": ["number", "expiry", "security_code"]
                },
                "paypal": {
                    "type": "object",
                    "properties": {
                        "email": {"type": "string"},
                        "country_code": {"type": "string"}
                    },
                    "required": ["email"]
                },
                "venmo": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"}
                    },
                    "required": ["user_id"]
                },
                "applepay": {
                    "type": "object",
                    "properties": {
                        "payment_token": {"type": "string"}
                    },
                    "required": ["payment_token"]
                }
            },
            "minProperties": 1
        }
    },
    "required": ["payment_source"]
}

def validate_json(data):
    try:
        validate(instance=data, schema=vault_schema)
        return "✅ JSON is valid!"
    except ValidationError as e:
        return f"❌ Validation Error: {e.message}"
