from fastapi import APIRouter, Depends, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from ..auth.dependencies import require_admin, get_current_user
from ..models.user import User
from ..models.role import Role
from ..database import get_db
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from fastapi.templating import Jinja2Templates
from ..services.session_service import generate_csrf
from ..security.security import hash_password
from ..security.validation import validate_username, validate_email, validate_password

router = APIRouter(prefix="/users", tags=["Users"])
templates = Jinja2Templates(directory="app/templates")


def _get_users_and_roles(db: Session):
    users = db.query(User).options(joinedload(User.role)).order_by(User.id).all()
    roles = db.query(Role).order_by(Role.id).all()
    return users, roles


@router.get("/", response_class=HTMLResponse)
@router.get("/config", response_class=HTMLResponse)
def users_list(
    request: Request,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    users, roles = _get_users_and_roles(db)
    csrf_token = generate_csrf()
    response = templates.TemplateResponse(
        "configUsers.html",
        {
            "request": request,
            "user": user,
            "users": users,
            "roles": roles,
            "csrf_token": csrf_token,
        },
    )
    response.set_cookie(key="csrf_token", value=csrf_token, httponly=True, samesite="lax")
    return response


@router.get("/create", response_class=HTMLResponse)
def create_user_form(
    request: Request,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    _, roles = _get_users_and_roles(db)
    csrf_token = generate_csrf()
    response = templates.TemplateResponse(
        "create_user.html",
        {
            "request": request,
            "user": user,
            "roles": roles,
            "csrf_token": csrf_token,
        },
    )
    response.set_cookie(key="csrf_token", value=csrf_token, httponly=True, samesite="lax")
    return response


@router.post("/create")
def create_user_post(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role_id: int = Form(...),
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    ok, err = validate_username(username)
    if not ok:
        _, roles = _get_users_and_roles(db)
        return templates.TemplateResponse(
            "create_user.html",
            {"request": request, "user": user, "roles": roles, "error": err, "csrf_token": request.cookies.get("csrf_token", "")},
            status_code=400,
        )
    ok, err = validate_email(email)
    if not ok:
        _, roles = _get_users_and_roles(db)
        return templates.TemplateResponse(
            "create_user.html",
            {"request": request, "user": user, "roles": roles, "error": err, "csrf_token": request.cookies.get("csrf_token", "")},
            status_code=400,
        )
    ok, err = validate_password(password)
    if not ok:
        _, roles = _get_users_and_roles(db)
        return templates.TemplateResponse(
            "create_user.html",
            {"request": request, "user": user, "roles": roles, "error": err, "csrf_token": request.cookies.get("csrf_token", "")},
            status_code=400,
        )
    if db.query(User).filter(User.username == username.strip()).first():
        _, roles = _get_users_and_roles(db)
        return templates.TemplateResponse(
            "create_user.html",
            {
                "request": request,
                "user": user,
                "roles": roles,
                "error": "El nombre de usuario ya existe.",
                "csrf_token": request.cookies.get("csrf_token", ""),
            },
            status_code=400,
        )
    if db.query(User).filter(User.email == email.strip().lower()).first():
        _, roles = _get_users_and_roles(db)
        return templates.TemplateResponse(
            "create_user.html",
            {
                "request": request,
                "user": user,
                "roles": roles,
                "error": "El email ya está registrado.",
                "csrf_token": request.cookies.get("csrf_token", ""),
            },
            status_code=400,
        )
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=400, detail="Rol no válido")
    new_user = User(
        username=username.strip(),
        email=email.strip().lower(),
        password_hash=hash_password(password),
        role_id=role_id,
    )
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/users/config", status_code=302)


@router.get("/{user_id}/edit", response_class=HTMLResponse)
def edit_user_form(
    request: Request,
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    edit_user = db.query(User).options(joinedload(User.role)).filter(User.id == user_id).first()
    if not edit_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    _, roles = _get_users_and_roles(db)
    csrf_token = generate_csrf()
    response = templates.TemplateResponse(
        "edit_user.html",
        {
            "request": request,
            "user": current_user,
            "edit_user": edit_user,
            "roles": roles,
            "csrf_token": csrf_token,
        },
    )
    response.set_cookie(key="csrf_token", value=csrf_token, httponly=True, samesite="lax")
    return response


@router.post("/{user_id}/edit")
def edit_user_post(
    request: Request,
    user_id: int,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(""),
    role_id: int = Form(...),
    is_active: str = Form("off"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    edit_user = db.query(User).options(joinedload(User.role)).filter(User.id == user_id).first()
    if not edit_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    ok, err = validate_username(username)
    if not ok:
        _, roles = _get_users_and_roles(db)
        return templates.TemplateResponse(
            "edit_user.html",
            {"request": request, "user": current_user, "edit_user": edit_user, "roles": roles, "error": err, "csrf_token": request.cookies.get("csrf_token", "")},
            status_code=400,
        )
    ok, err = validate_email(email)
    if not ok:
        _, roles = _get_users_and_roles(db)
        return templates.TemplateResponse(
            "edit_user.html",
            {"request": request, "user": current_user, "edit_user": edit_user, "roles": roles, "error": err, "csrf_token": request.cookies.get("csrf_token", "")},
            status_code=400,
        )
    if password and password.strip():
        ok, err = validate_password(password)
        if not ok:
            _, roles = _get_users_and_roles(db)
            return templates.TemplateResponse(
                "edit_user.html",
                {"request": request, "user": current_user, "edit_user": edit_user, "roles": roles, "error": err, "csrf_token": request.cookies.get("csrf_token", "")},
                status_code=400,
            )
    other = db.query(User).filter(User.username == username.strip(), User.id != user_id).first()
    if other:
        _, roles = _get_users_and_roles(db)
        return templates.TemplateResponse(
            "edit_user.html",
            {
                "request": request,
                "user": current_user,
                "edit_user": edit_user,
                "roles": roles,
                "error": "El nombre de usuario ya existe.",
                "csrf_token": request.cookies.get("csrf_token", ""),
            },
            status_code=400,
        )
    other_email = db.query(User).filter(User.email == email.strip().lower(), User.id != user_id).first()
    if other_email:
        _, roles = _get_users_and_roles(db)
        return templates.TemplateResponse(
            "edit_user.html",
            {
                "request": request,
                "user": current_user,
                "edit_user": edit_user,
                "roles": roles,
                "error": "El email ya está en uso.",
                "csrf_token": request.cookies.get("csrf_token", ""),
            },
            status_code=400,
        )
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=400, detail="Rol no válido")
    edit_user.username = username.strip()
    edit_user.email = email.strip().lower()
    edit_user.role_id = role_id
    edit_user.is_active = is_active == "on"
    if password and password.strip():
        edit_user.password_hash = hash_password(password)
    db.commit()
    return RedirectResponse(url="/users/config", status_code=302)


@router.post("/{user_id}/delete")
def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propio usuario")
    edit_user = db.query(User).filter(User.id == user_id).first()
    if not edit_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(edit_user)
    db.commit()
    return RedirectResponse(url="/users/config", status_code=302)
