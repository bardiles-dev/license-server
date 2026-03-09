from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import base64
import uuid

from ..database import get_db
from ..models import LicenseRecord, User
from ..schemas import LicenseCreate, LicenseRenew
from ..crypto import sign_license
from ..auth.dependencies import get_current_user


def _validate_license_id(license_id: str) -> None:
    """Asegura que license_id tenga formato UUID para evitar inyección en path."""
    try:
        uuid.UUID(license_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="license_id must be a valid UUID")

router = APIRouter(tags=["License Authority"])

ISSUER_NAME = "Technology Solutions"
SIGNATURE_ALGORITHM = "RSA-SHA256"

# Misma serialización que crypto.sign_license para que verify en license-server coincida
JSON_DUMPS_KW = {"sort_keys": True, "separators": (",", ":")}

# Formato de features: clave = id de herramienta/módulo, valor = atributos (version, funcionality, etc.)
DEFAULT_FEATURES = {
    "ia-agent": {
        "version": "2026.1",
        "funcionality": "HU,EXEC,QA-AGENT",
    },
}


def encode_license_to_string(payload: dict, signature: str) -> str:
    """
    Codifica el license_blob completo (payload + signature) en un único string base64url.
    Sin delimitadores: el cliente pega este string en license-server y se decodifica
    al mismo JSON que firmó la authority, así la verificación de firma siempre pasa.
    Seguro para formularios (base64url no usa + ni /).
    """
    license_blob = {"payload": payload, "signature": signature}
    blob_bytes = json.dumps(license_blob, **JSON_DUMPS_KW).encode("utf-8")
    return base64.urlsafe_b64encode(blob_bytes).decode("ascii").rstrip("=")


def utc_now():
    return datetime.utcnow().replace(microsecond=0)


def utc_iso(dt: datetime):
    return dt.isoformat() + "Z"


def save_license(
    db: Session,
    payload: dict,
    previous_license_id=None,
    version=1
):
    record = LicenseRecord(
        license_id=payload["license_id"],
        previous_license_id=previous_license_id,
        company=payload["company"],
        license_type=payload["type"],
        max_activations=payload["max_activations"],
        machine_lock=payload["machine_lock"],
        issued_at=datetime.fromisoformat(payload["issued_at"].replace("Z", "")),
        expires_at=datetime.fromisoformat(payload["expires_at"].replace("Z", "")),
        status=payload["status"],
        version=version
    )
    db.add(record)
    db.commit()
    db.refresh(record)


def _features_to_dict(features_list) -> dict:
    """Convierte List[FeatureItem] al dict { tool_id: { ...attrs } } del payload."""
    if not features_list:
        return DEFAULT_FEATURES
    out = {}
    for item in features_list:
        d = item.model_dump(exclude_none=True)
        tid = d.pop("id", None)
        if tid:
            out[tid] = d
    return out if out else DEFAULT_FEATURES


def _build_payload(data: LicenseCreate, now: datetime, expires: datetime, license_id: str, version: int = 1, **overrides):
    features = _features_to_dict(data.features)
    base = {
        "license_id": license_id,
        "issuer": ISSUER_NAME,
        "signature_algorithm": SIGNATURE_ALGORITHM,
        "version": version,
        "company": data.company.replace(" ", "-"),
        "type": data.license_type.value,
        "max_activations": data.max_activations,
        "machine_lock": data.machine_lock,
        "features": features,
        "issued_at": utc_iso(now),
        "expires_at": utc_iso(expires),
        "status": "active",
    }
    base.update(overrides)
    return base


@router.post("/create")
def create_license(
    data: LicenseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Crea una licencia y devuelve payload, firma y string para instalar en license-server."""
    now = utc_now()
    expires = now + timedelta(days=data.duration_days)
    license_id = str(uuid.uuid4())

    payload = _build_payload(data, now, expires, license_id)
    signature = sign_license(payload)
    save_license(db, payload)

    license_install_string = encode_license_to_string(payload, signature)

    return {
        "payload": payload,
        "signature": signature,
        "license_install_string": license_install_string,
    }


@router.post("/create-license")
def create_license_backup(
    data: LicenseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Respaldo de /create: misma lógica, devuelve payload, firma y string instalable."""
    now = utc_now()
    expires = now + timedelta(days=data.duration_days)
    license_id = str(uuid.uuid4())

    payload = _build_payload(data, now, expires, license_id)
    signature = sign_license(payload)
    save_license(db, payload)

    license_install_string = encode_license_to_string(payload, signature)

    return {
        "payload": payload,
        "signature": signature,
        "license_install_string": license_install_string,
    }


@router.post("/renew/{license_id}")
def renew_license(
    license_id: str,
    renew_data: LicenseRenew,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _validate_license_id(license_id)
    existing = db.query(LicenseRecord).filter(
        LicenseRecord.license_id == license_id,
        LicenseRecord.status == "active"
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="License not found or not active")

    existing.status = "revoked"
    db.commit()

    now = utc_now()
    expires = now + timedelta(days=renew_data.extra_days)
    new_version = existing.version + 1
    new_license_id = str(uuid.uuid4())

    new_payload = {
        "license_id": new_license_id,
        "issuer": ISSUER_NAME,
        "signature_algorithm": SIGNATURE_ALGORITHM,
        "version": new_version,
        "company": existing.company,
        "type": existing.license_type,
        "max_activations": existing.max_activations,
        "machine_lock": existing.machine_lock,
        "features": DEFAULT_FEATURES,
        "issued_at": utc_iso(now),
        "expires_at": utc_iso(expires),
        "status": "active",
    }

    signature = sign_license(new_payload)
    save_license(
        db,
        new_payload,
        previous_license_id=existing.license_id,
        version=new_version
    )

    license_install_string = encode_license_to_string(new_payload, signature)

    return {
        "payload": new_payload,
        "signature": signature,
        "license_install_string": license_install_string,
    }


@router.post("/revoke/{license_id}")
def revoke_license(
    license_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _validate_license_id(license_id)
    existing = db.query(LicenseRecord).filter(
        LicenseRecord.license_id == license_id,
        LicenseRecord.status == "active"
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="License not found or already revoked")

    existing.status = "revoked"
    db.commit()
    return {"message": f"License {license_id} revoked successfully"}


@router.get("/licenses")
def list_licenses(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return db.query(LicenseRecord).all()
