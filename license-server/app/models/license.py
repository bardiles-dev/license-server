import json
from sqlalchemy import Column, String, Integer, DateTime
from datetime import datetime
from ..database import Base

# Formato: JSON string de { "tool-id": { "version": "...", "funcionality": "..." } }
DEFAULT_FEATURES = json.dumps({
    "ia-agent": {"version": "2026.1", "funcionality": "HU,EXEC,QA-AGENT"},
})


class InstalledLicense(Base):
    __tablename__ = "installed_licenses"

    license_key = Column(String, primary_key=True)
    company = Column(String)
    license_type = Column(String)  # machine | floating
    max_activations = Column(Integer)
    machine_lock = Column(String, nullable=True)
    expires_at = Column(DateTime)
    status = Column(String)
    features = Column(String, default=DEFAULT_FEATURES, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ActiveSession(Base):
    __tablename__ = "active_sessions"

    session_id = Column(String, primary_key=True)
    license_key = Column(String)
    machine_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
