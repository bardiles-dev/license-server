from datetime import datetime


EXPECTED_ISSUER = "MyCompany License Authority"
SUPPORTED_VERSIONS = [1]


def validate_payload_structure(payload: dict):

    required_fields = [
        "license_id",
        "issuer",
        "signature_algorithm",
        "version",
        "company",
        "type",
        "max_activations",
        "issued_at",
        "expires_at",
        "status"
    ]

    for field in required_fields:
        if field not in payload:
            return False, f"Missing field {field}"

    return True, None


def validate_business_rules(payload: dict):

    if payload["issuer"] != EXPECTED_ISSUER:
        return False, "Invalid issuer"

    if payload["version"] not in SUPPORTED_VERSIONS:
        return False, "Unsupported license version"

    expires = datetime.fromisoformat(
        payload["expires_at"].replace("Z", "")
    )

    if datetime.utcnow() > expires:
        return False, "License expired"

    if payload["status"] != "active":
        return False, "License not active"

    return True, None
