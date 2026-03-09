from fastapi import APIRouter, Depends, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from ..auth.dependencies import require_admin, get_current_user
from ..models.user import User
from ..database import get_db
from sqlalchemy.orm import Session
from ..models.license import InstalledLicense
from datetime import datetime
from ..security.security import verify_license_signature, decode_payload
from ..security.validation import sanitize_license_install_string

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/only")
def admin_area(user: User = Depends(require_admin)):
    return {"message": "Admin access granted"}


@router.post("/delete-license/{license_key}")
def delete_license(
    license_key: str,
    request: Request,
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin)  # ya valida autenticación y rol
):  
    cookie_token = request.cookies.get("csrf_token")

    if not cookie_token or cookie_token != csrf_token:
        raise HTTPException(status_code=403, detail="CSRF validation failed")
    
    license_obj = db.query(InstalledLicense).filter(
        InstalledLicense.license_key == license_key
    ).first()

    if not license_obj:
        raise HTTPException(
            status_code=404,
            detail="License not found"
        )

    db.delete(license_obj)
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)  


@router.post("/install-license")
def install_license(
    request: Request,
    license_key_install: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin)):
    cookie_token = request.cookies.get("csrf_token")
    if not cookie_token or cookie_token != csrf_token:
        raise HTTPException(status_code=403, detail="CSRF validation failed")

    raw = sanitize_license_install_string(license_key_install)
    if not raw:
        raise HTTPException(status_code=400, detail="License string empty or too long")

    license_blob = decode_payload(raw)
    payload = verify_license_signature(license_blob)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid license signature")
    
    #db.query(InstalledLicense).delete()
    new_license = InstalledLicense(
        license_key=payload["license_id"],
        company=payload["company"],
        license_type=payload["type"],
        max_activations=payload["max_activations"],
        machine_lock=payload.get("machine_lock"),
        expires_at=datetime.fromisoformat(
            payload["expires_at"].replace("Z", "")
        ),
        status=payload.get("status", "active")
    )

    db.add(new_license)
    db.commit()
    response = RedirectResponse(url="/", status_code=302)

    return response