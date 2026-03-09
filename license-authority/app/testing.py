import json
import base64
import hashlib
import uuid
import platform


def get_fingerprint():
    raw_data = f"{platform.node()}-{uuid.getnode()}-{platform.system()}"
    return hashlib.sha256(raw_data.encode()).hexdigest()


def decodePayload(license_string: str) -> dict:
    """
    Decodifica el string de licencia (base64url del license_blob JSON).
    Mismo formato que license-server: devuelve {payload, signature}.
    """
    raw = license_string.strip()
    pad = 4 - (len(raw) % 4)
    if pad != 4:
        raw += "=" * pad
    blob_bytes = base64.urlsafe_b64decode(raw)
    license_blob = json.loads(blob_bytes.decode("utf-8"))
    if "payload" not in license_blob or "signature" not in license_blob:
        raise ValueError("Formato de licencia inválido")
    return license_blob


if __name__ == "__main__":
    from app.routes.license_routes import encode_license_to_string

    jsonLoad = '''{
        "license_blob": {
            "payload": {
                "license_id": "7df87fc4-8137-4083-89ad-8533bd897356",
                "issuer": "MyCompany License Authority",
                "signature_algorithm": "RSA-SHA256",
                "version": 1,
                "company": "ptrickbtman-sa",
                "type": "floating",
                "max_activations": 5,
                "machine_lock": null,
                "features": {
                    "additionalProp1": {
                        "versionSfw": "1"
                    }
                },
                "issued_at": "2026-02-18T18:18:04Z",
                "expires_at": "2027-02-18T18:18:04Z",
                "status": "active"
            },
            "signature": "W7lngo/rxFrshpKMS7waDVnlWkBndm8lVYeFySbvIJAYZdMbuRprs541/19+CbRqV37UyMWU6e+NcQLUdS6mPc5uO/v6yx+YeCtPBpzWT0JAfifqk2FYe0NUT1EpwfW58w1KiH2uXJMF9Zcst22HBTQ5OOMADhxEWapRPpKTha/g7yl005KhggYSQ8scsfiNhsgY07iF76VtOcNHZsnTFplduAEmLTgFZRmPIjOFYFa+aqC4WW7PSAul3lJS+M4ToyF6Uv91DPXr7Q5kuUlsLFKIIZJ0v66NQJ8A4lRxNAFpdri8BSlXZ0wcQiVh/0kyH1izA+dRB0/mfKnxbFiu7A=="
        }
    }'''

    # Convertir JSON string a dict
    data = json.loads(jsonLoad)
    payload = data["license_blob"]["payload"]
    signature = data["license_blob"]["signature"]

    # String instalable (base64url): se pega en license-server /install-from-string
    readLicense = encode_license_to_string(payload, signature)
    print("license_install_string:", readLicense)
    decoded = decodePayload(readLicense)
    print("decoded license_blob keys:", list(decoded.keys()))
    print(get_fingerprint())

    

# # DECIFRARR
# issued_at_ts = int(
#     datetime.fromisoformat(payload["issued_at"].replace("Z", "+00:00")).timestamp()
# )

# expires_at_ts = int(
#     datetime.fromisoformat(payload["expires_at"].replace("Z", "+00:00")).timestamp()
# )



