from pathlib import Path

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import LicenseRecord, User
from ..auth.dependencies import get_current_user

router = APIRouter()
_templates_dir = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))


@router.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    licenses = db.query(LicenseRecord).order_by(LicenseRecord.created_at.desc()).all()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user,
        "licenses": licenses,
    })
