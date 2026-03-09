from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models.license import InstalledLicense
from ..config import (
    LICENSE_STATUS_ACTIVE,
    LICENSE_STATUS_EXPIRED,
    LICENSE_STATUS_REVOKED
)


def get_license(db: Session, license_key: str):
    return db.query(InstalledLicense).filter(
        InstalledLicense.license_key == license_key
    ).first()


def validate_license_state(license):
    if not license:
        return False, "License not found"

    if license.status == LICENSE_STATUS_REVOKED:
        return False, "License revoked"

    if datetime.utcnow() > license.expires_at:
        license.status = LICENSE_STATUS_EXPIRED
        return False, "License expired"

    return True, None


def renew_license(db: Session, license_key: str, extra_days: int):
    license = get_license(db, license_key)
    if not license:
        return False

    license.expires_at += timedelta(days=extra_days)
    db.commit()
    return True


def revoke_license(db: Session, license_key: str):
    license = get_license(db, license_key)
    if not license:
        return False
    license.status = LICENSE_STATUS_REVOKED
    db.commit()
    return True



def delete_license(db: Session, license_key: str):
    return db.query(InstalledLicense).filter(
        InstalledLicense.license_key == license_key
    ).delete()


def update_license_status(db: Session, license_key: str, status: str):
    return db.query(InstalledLicense).filter(
        InstalledLicense.license_key == license_key
    ).update({
        "status": status
    })


def delete_expired_licenses(db: Session):
    return db.query(InstalledLicense).filter(
        InstalledLicense.expires_at < datetime.utcnow()
    ).delete()