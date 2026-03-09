import uuid
from datetime import datetime, timedelta
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
