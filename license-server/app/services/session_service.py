import uuid
from datetime import datetime, timedelta
from typing import Tuple
from sqlalchemy.orm import Session
from ..models.license import ActiveSession
from ..config import SESSION_TIMEOUT_MINUTES
import secrets

def cleanup_sessions(db: Session):

    now = datetime.utcnow()

    db.query(ActiveSession).filter(
        ActiveSession.expires_at < now
    ).delete()

    db.commit()


def find_active_session(db: Session, license_key: str, machine_id: str):
    """Devuelve la sesión activa (no expirada) para license_key + machine_id, o None."""
    now = datetime.utcnow()
    return db.query(ActiveSession).filter(
        ActiveSession.license_key == license_key,
        ActiveSession.machine_id == machine_id,
        ActiveSession.expires_at > now,
    ).first()


def update_session_expiry(db: Session, session: ActiveSession) -> str:
    """Actualiza last_seen y expires_at de la sesión (refresh). Devuelve session_id."""
    now = datetime.utcnow()
    session.last_seen = now
    session.expires_at = now + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    db.commit()
    return session.session_id


def activate_or_refresh_session(db: Session, license_key: str, machine_id: str) -> Tuple[str, bool]:
    """
    Si ya existe una sesión activa para (license_key, machine_id), la actualiza y devuelve (session_id, True).
    Si no, crea una nueva y devuelve (session_id, False).
    """
    existing = find_active_session(db, license_key, machine_id)
    if existing:
        session_id = update_session_expiry(db, existing)
        return session_id, True
    session_id = create_session(db, license_key, machine_id)
    return session_id, False


def generate_csrf():
    return secrets.token_urlsafe(32)

    
def create_session(db: Session, license_key: str, machine_id: str):

    now = datetime.utcnow()

    session = ActiveSession(
        session_id=str(uuid.uuid4()),
        license_key=license_key,
        machine_id=machine_id,
        created_at=now,
        last_seen=now,
        expires_at=now + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    )

    db.add(session)
    db.commit()

    return session.session_id
