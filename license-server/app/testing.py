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




if __name__ == "__main__":
    def json = {
        "license_blob": {
            "payload": {
            "license_id": "7df87fc4-8137-4083-89ad-8533bd897356",
            "issuer": "MyCompany License Authority",
            "signature_algorithm": "RSA-SHA256",
            "version": 1,
            "company": "ptrickbtman sa",
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
    }


    license_json = generate_install_license(json)
    print(json.dumps(license_json, indent=2))