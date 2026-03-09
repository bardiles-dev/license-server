import json
from fastapi import APIRouter, Depends, HTTPException, Form, Request, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime
import re
from ..database import get_db
from ..schemas.license import LicenseInstall, LicenseActivate
from ..models.license import InstalledLicense, ActiveSession
from ..models.user import User
from ..auth.dependencies import require_admin
from ..security.security import verify_license_signature, decode_payload
from ..security.validation import sanitize_license_install_string
from ..services.license_service import get_license, validate_license_state
from ..services.session_service import cleanup_sessions, create_session

router = APIRouter(prefix="/api/license", tags=["License API"])

# Redirecciones fijas (evitar open redirect)
REDIRECT_ROOT = "/"
REDIRECT_ERROR_CSRF = "/?error=csrf"
REDIRECT_ERROR_EMPTY = "/?error=empty"
REDIRECT_ERROR_DECODE = "/?error=decode"
REDIRECT_ERROR_SIGNATURE = "/?error=signature"
REDIRECT_INSTALLED = "/?installed=1"


DEFAULT_FEATURES_MAP = {"ia-agent": {"version": "2026.1", "funcionality": "HU,EXEC,QA-AGENT"}}


def _features_from_payload(payload: dict) -> str:
    """
    Normaliza features del payload a un dict (formato tools) y devuelve JSON string.
    Acepta: nuevo formato { "ia-agent": { "version": "...", "funcionality": "..." } }
    o legacy additionalProp1.
    """
    raw = payload.get("features")
    if isinstance(raw, str):
        return raw.strip() or json.dumps(DEFAULT_FEATURES_MAP)
    if isinstance(raw, dict):
        # Formato nuevo: { "tool-id": { "version": "...", ... } }
        if any(k != "additionalProp1" for k in raw.keys()):
            return json.dumps(raw)
        # Legacy: additionalProp1
        prop = raw.get("additionalProp1")
        if isinstance(prop, dict):
            tool_id = prop.get("tool", "ia-agent")
            normalized = {
                tool_id: {
                    "version": prop.get("Version", prop.get("version", "")),
                    "funcionality": prop.get("funcionality", "HU,EXEC,QA-AGENT"),
                }
            }
            return json.dumps(normalized)
    return json.dumps(DEFAULT_FEATURES_MAP)


def _install_license_from_payload(db: Session, payload: dict) -> None:
    """Instala o actualiza una licencia en BD (upsert por license_key)."""
    license_key = payload["license_id"]
    features_str = _features_from_payload(payload)
    expires_at = datetime.fromisoformat(payload["expires_at"].replace("Z", ""))
    data = {
        "company": payload["company"],
        "license_type": payload["type"],
        "max_activations": payload["max_activations"],
        "machine_lock": payload.get("machine_lock") or None,
        "expires_at": expires_at,
        "status": payload.get("status", "active"),
        "features": features_str,
    }
    existing = db.query(InstalledLicense).filter(InstalledLicense.license_key == license_key).first()
    if existing:
        for key, value in data.items():
            setattr(existing, key, value)
    else:
        new_license = InstalledLicense(license_key=license_key, **data)
        db.add(new_license)
    db.commit()


@router.post("/install")
def install_license(data: LicenseInstall, db: Session = Depends(get_db)):
    payload = verify_license_signature(data.license_blob)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid license signature")
    _install_license_from_payload(db, payload)
    return {"status": "license installed"}


@router.post("/install-from-string")
def install_license_from_string(
    request: Request,
    license_key_install: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    """Recibe el string de license-authority (license_install_string), decodifica, verifica firma e instala."""
    cookie_token = request.cookies.get("csrf_token")
    if not cookie_token or cookie_token != csrf_token:
        return RedirectResponse(url=REDIRECT_ERROR_CSRF, status_code=302)
    
    pattern = r"^([A-Za-z0-9]+_[A-Za-z0-9]+|[A-Za-z0-9]+-[A-Za-z0-9]+_[A-Za-z0-9]+)$"
    if not re.match(pattern, license_key_install):
        return RedirectResponse(url=REDIRECT_ERROR_DECODE, status_code=302)

    license_key_install = license_key_install.split("_")[1]
    raw = sanitize_license_install_string(license_key_install)
    if not raw:
        return RedirectResponse(url=REDIRECT_ERROR_EMPTY, status_code=302)

    try:
        license_blob = decode_payload(raw)
        payload = verify_license_signature(license_blob)
        if not payload:
            return RedirectResponse(url=REDIRECT_ERROR_SIGNATURE, status_code=302)
        _install_license_from_payload(db, payload)
        return RedirectResponse(url=REDIRECT_INSTALLED, status_code=302)
    except (ValueError, KeyError, TypeError):
        return RedirectResponse(url=REDIRECT_ERROR_DECODE, status_code=302)


@router.get("/licenses")
def get_all_licenses(db: Session = Depends(get_db)):
    licenses = db.query(InstalledLicense).all()
    return licenses


def _license_info_response(license_obj):
    """Construye la respuesta con datos de licencia y features para el cliente."""
    try:
        features = json.loads(license_obj.features or "{}")
    except (TypeError, ValueError):
        features = {}
    return {
        "company": license_obj.company,
        "license_type": license_obj.license_type,
        "expires_at": license_obj.expires_at.isoformat() if license_obj.expires_at else None,
        "features": features,
    }


@router.post("/activate")
def activate_license(data: LicenseActivate, db: Session = Depends(get_db)):
    """
    Activa una licencia para una máquina. El cliente envía license_key y machine_id (fingerprint de la máquina).
    Devuelve session_id y los datos de la licencia (company, expires_at, features) para que la app consumidora
    no necesite una segunda llamada.
    """
    cleanup_sessions(db)
    license_obj = get_license(db, data.license_key)
    valid, error = validate_license_state(license_obj)
    if not valid:
        raise HTTPException(status_code=400, detail=error or "License invalid")
    if license_obj.license_type == "machine":
        if license_obj.machine_lock != data.machine_id:
            raise HTTPException(status_code=400, detail="Machine mismatch: esta licencia está vinculada a otra máquina (machine_lock)")
    elif license_obj.license_type == "floating":
        active = db.query(ActiveSession).filter(ActiveSession.license_key == data.license_key).count()
        if active >= license_obj.max_activations:
            raise HTTPException(status_code=400, detail="No licenses available (max_activations reached)")
    session_id = create_session(db, data.license_key, data.machine_id)
    out = {"status": "activated", "session_id": session_id}
    out.update(_license_info_response(license_obj))
    return out


@router.get("/status")
def license_status(
    license_key: str = Query(None),
    machine_id: str = Query(None),
    session_id: str = Query(None),
    db: Session = Depends(get_db),
):
    """
    Obtiene los datos de la licencia (company, expires_at, features) para una app consumidora.
    Opción 1: enviar session_id (obtenido al activar) en query.
    Opción 2: enviar license_key y machine_id (misma validación que activate, pero sin crear sesión).
    """
    if session_id:
        session = db.query(ActiveSession).filter(ActiveSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        license_obj = get_license(db, session.license_key)
    elif license_key and machine_id:
        license_obj = get_license(db, license_key)
        valid, error = validate_license_state(license_obj)
        if not valid:
            raise HTTPException(status_code=400, detail=error or "License invalid")
        if license_obj.license_type == "machine" and license_obj.machine_lock != machine_id:
            raise HTTPException(status_code=400, detail="Machine mismatch")
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either session_id or both license_key and machine_id",
        )
    return _license_info_response(license_obj)