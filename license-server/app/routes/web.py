import json
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from ..database import get_db
from ..models.license import InstalledLicense, ActiveSession
from ..models.user import User
from ..auth.dependencies import get_current_user
from ..services.session_service import generate_csrf
from ..security.validation import allowlist_install_error

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _parse_features_display(features_str):
    """Convierte el JSON de features en lista de dicts para mostrar en el dashboard."""
    if not features_str or not features_str.strip():
        return []
    try:
        data = json.loads(features_str)
        if not isinstance(data, dict):
            return [{"tool": "-", "attrs": str(data)}]
        out = []
        for tool_id, attrs in data.items():
            if isinstance(attrs, dict):
                out.append({"tool": tool_id, "attrs": attrs})
            else:
                out.append({"tool": tool_id, "attrs": {"value": attrs}})
        return out
    except (json.JSONDecodeError, TypeError):
        return [{"tool": "-", "attrs": {"value": features_str}}]


@router.get("/", response_class=HTMLResponse)
@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    licenses = db.query(InstalledLicense).order_by(InstalledLicense.expires_at.desc()).all()
    licenses_with_features = [(lic, _parse_features_display(lic.features)) for lic in licenses]
    sessions = db.query(ActiveSession).all()
    csrf_token = generate_csrf()
    forbidden = request.query_params.get("forbidden") == "1"
    installed = request.query_params.get("installed") == "1"
    # Solo valores permitidos para evitar XSS reflejado vía ?error=
    install_error = allowlist_install_error(request.query_params.get("error"))

    response = templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "licenses": list(licenses),
        "licenses_with_features": licenses_with_features,
        "sessions": sessions,
        "csrf_token": csrf_token,
        "forbidden": forbidden,
        "installed": installed,
        "install_error": install_error,
    })
    
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        path="/",
        httponly=True,
        samesite="lax"
    )
    
    return response