from fastapi import Request, HTTPException, Depends, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..security.security import decode_token


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
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
    if not user:
        raise HTTPException(status_code=401)

    return user


def require_admin(
    user: User = Depends(get_current_user)
):
    if user.role.name != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user