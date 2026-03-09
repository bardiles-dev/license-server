from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    """Usuario para login en License Authority (inspirado en license-server)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class LicenseRecord(Base):
    __tablename__ = "license_records"

    id = Column(Integer, primary_key=True)

    license_id = Column(String, unique=True, index=True)
    previous_license_id = Column(String, nullable=True)

    company = Column(String)

    license_type = Column(String)
    max_activations = Column(Integer)
    machine_lock = Column(String, nullable=True)

    issued_at = Column(DateTime)
    expires_at = Column(DateTime)

    revoked = Column(Boolean, default=False)
    version = Column(Integer, default=1)
   
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active")