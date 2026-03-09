import json
import base64
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key

_PEM_PATH = os.environ.get("PUBLIC_PEM_PATH", "public.pem")
with open(_PEM_PATH, "rb") as f:
    PUBLIC_KEY = load_pem_public_key(f.read())


SUPPORTED_ALGORITHMS = ["RSA-SHA256"]


def verify_signature(payload: dict, signature: str, algorithm: str):

    if algorithm not in SUPPORTED_ALGORITHMS:
        return False

    payload_bytes = json.dumps(
        payload,
        sort_keys=True
    ).encode()

    signature_bytes = base64.b64decode(signature)

    try:
        PUBLIC_KEY.verify(
            signature_bytes,
            payload_bytes,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False




def generate_license():
    payload = {
        "license_id": str(uuid.uuid4()),
        "issuer": "MyCompany License Authority",
        "signature_algorithm": "RSA-SHA256",
        "version": 1,
        "company": "ptrickbtman sa",
        "type": "floating",
        "max_activations": 5,
        "machine_lock": None,
        "features": {
            "additionalProp1": {
                "versionSfw": "1"
            }
        },
        "issued_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "active"
    }

    # 🔁 Serializar SIEMPRE ordenado
    payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")

    # ✍️ Firmar
    signature = private_key.sign(
        payload_bytes,
        padding.PKCS1v15(),
        hashes.SHA256()
    )

    # 📦 Base64
    signature_b64 = base64.b64encode(signature).decode()

    license_blob = {
        "license_blob": {
            "payload": payload,
            "signature": signature_b64
        }
    }

    return license_blob