from fastapi import FastAPI, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from datetime import datetime

from .database import Base, engine, get_db
from .schemas.license import (
    LicenseActivate,
    LicenseDeactivate,
    LicenseRenew,
    LicenseRevoke,
    LicenseInstall,
)
from .services.license_service import (
    get_license,
    validate_license_state,
    renew_license,
    revoke_license
)

from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from .auth.dependencies import get_current_user, require_admin

from .services.session_service import create_session, cleanup_sessions
from .models.license import (ActiveSession, InstalledLicense)
from .security.security import verify_license_signature, hash_password, verify_password, create_access_token

from .models.user import User
from .models.role import Role

app = FastAPI()

# ------------------------------------------
# WEB SITE CONFIGURATION

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

Base.metadata.create_all(bind=engine)


# ---------- INIT ROLES ----------

@app.on_event("startup")
def create_default_admin():
    db = next(get_db())
    if not db.query(User).first():
        print("-- Generando Tabla Admin")
        role = db.query(Role).filter(Role.name == "admin").first()
        user = User(
            username="admin",
            email="admin@local",
            password_hash=hash_password("admin"),
            role=role
        )
        db.add(user)
        db.commit()



@app.on_event("startup")
def create_default_roles():
    db = next(get_db())
    if not db.query(Role).filter(Role.name == "admin").first():
        print("-- Generando Tabla roles")
        db.add(Role(name="admin", description="Full access"))
        db.add(Role(name="support", description="Limited access"))
        db.commit()
        
        
# END STARTUP LICENSE

@app.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    user: User = Depends(get_current_user),  # 🔒 PROTECCIÓN
    db: Session = Depends(get_db)
):
    license = db.query(InstalledLicense).first()
    sessions = db.query(ActiveSession).all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "license": license,
        "sessions": sessions
    })

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    user: User = Depends(get_current_user),  # 🔒 PROTECCIÓN
    db: Session = Depends(get_db)
):
    license = db.query(InstalledLicense).first()
    sessions = db.query(ActiveSession).all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "license": license,
        "sessions": sessions
    })

# --------------------------------------------
# APP LOGIN



# ---------- CREATE ADMIN (SOLO PRIMERA VEZ) ----------
@app.post("/create-admin")
def create_admin(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):

    role = db.query(Role).filter(Role.name == "admin").first()

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role=role
    )

    db.add(user)
    db.commit()

    return {"status": "admin created"}


# ---------- LOGIN ----------
@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {
        "request": request
    })

@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()

    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid credentials"
        })

    token = create_access_token({"sub": user.username})

    response = RedirectResponse(url="/", status_code=302)

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,  # TRUE en producción
        samesite="lax"
    )

    return response


# ---------- LOGOUT ----------
@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response


# ---------- DASHBOARD PROTEGIDO ----------
@app.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    license = db.query(InstalledLicense).first()
    sessions = db.query(ActiveSession).all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "license": license,
        "sessions": sessions
    })

# ---------- EJEMPLO RUTA SOLO ADMIN ----------
@app.get("/admin-only")
def admin_area(user: User = Depends(require_admin)):
    return {"message": "Admin access granted"}



# --------------------------------------------
# LICENSE ROUTES API

@app.post("/install-license")
def install_license(data: LicenseInstall, db: Session = Depends(get_db)):

    payload = verify_license_signature(data.license_blob)

    if not payload:
        raise HTTPException(status_code=400, detail="Invalid license signature")

    # borra licencia anterior
    db.query(InstalledLicense).delete()

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

    return {"status": "license installed"}




@app.post("/activate")
def activate(data: LicenseActivate, db: Session = Depends(get_db)):

    cleanup_sessions(db)

    license = get_license(db, data.license_key)

    valid, error = validate_license_state(license)

    if not valid:
        raise HTTPException(status_code=400, detail=error)

    if license.license_type == "machine":

        if license.machine_lock != data.machine_id:
            raise HTTPException(status_code=400, detail="Machine mismatch")

    if license.license_type == "floating":

        active = db.query(ActiveSession).filter(
            ActiveSession.license_key == data.license_key
        ).count()

        if active >= license.max_activations:
            raise HTTPException(status_code=400, detail="No licenses available")

    session_id = create_session(db, data.license_key, data.machine_id)

    return {"status": "activated", "session_id": session_id}


@app.post("/deactivate")
def deactivate(data: LicenseDeactivate, db: Session = Depends(get_db)):

    db.query(ActiveSession).filter(
        ActiveSession.license_key == data.license_key,
        ActiveSession.machine_id == data.machine_id
    ).delete()

    db.commit()

    return {"status": "deactivated"}


@app.post("/renew")
def renew(data: LicenseRenew, db: Session = Depends(get_db)):

    ok = renew_license(db, data.license_key, data.extra_days)

    if not ok:
        raise HTTPException(status_code=400, detail="License not found")

    return {"status": "renewed"}


    

@app.post("/revoke")
def revoke(data: LicenseRevoke, db: Session = Depends(get_db)):

    ok = revoke_license(db, data.license_key)

    if not ok:
        raise HTTPException(status_code=400, detail="License not found")

    return {"status": "revoked"}


