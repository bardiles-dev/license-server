import json
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key

PRIVATE_KEY_PATH = "keys/private.pem"


def load_private_key():
    with open(PRIVATE_KEY_PATH, "rb") as key_file:
        return load_pem_private_key(key_file.read(), password=None)


def sign_license(payload: dict) -> str:
    private_key = load_private_key()

    payload_bytes = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":")
    ).encode()

    signature = private_key.sign(
        payload_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    return base64.b64encode(signature).decode()