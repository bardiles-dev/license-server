import json
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone


# READ USER-SECURITY
import os

SECRET_KEY = os.environ.get("SECRET_KEY", "Secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas para evitar expirar en medio de uso

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": now
    })

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None



# ** Lectura de public.pem y comparativa con el signature procesado para la validacion de licencia
# READ LICENSE SECURITY


def load_public_key():
    path = os.environ.get("PUBLIC_PEM_PATH", "./public.pem")
    with open(path, "rb") as f:
        return serialization.load_pem_public_key(f.read())


def decode_payload(license_string: str) -> dict:
    """
    Decodifica el string de licencia (base64url del license_blob JSON).
    Devuelve el mismo dict {payload, signature} que firmó license-authority,
    para pasarlo a verify_license_signature sin reconstruir nada.
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


def verify_license_signature(license_blob):
    """Verifica la firma RSA-PSS del license_blob. El payload debe coincidir con el que firmó la authority (mismo issuer, features, serialización)."""
    try:
        if isinstance(license_blob, str):
            license_data = json.loads(license_blob)
        else:
            license_data = license_blob
        payload = license_data["payload"]
        signature = base64.b64decode(license_data["signature"])
        public_key = load_public_key()
        payload_bytes = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":")
        ).encode()
        public_key.verify(
            signature,
            payload_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return payload
    except InvalidSignature:
        return None
    except Exception:
        return None
