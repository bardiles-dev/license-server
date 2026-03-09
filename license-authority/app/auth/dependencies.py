"""Dependencia para obtener usuario actual desde cookie (como en license-server)."""
from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..security.auth import decode_token


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401)
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401)
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401)
    return user
