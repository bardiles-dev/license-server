from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any

# Límites para evitar payloads enormes e inyección en APIs
LICENSE_KEY_MAX_LEN = 64
MACHINE_ID_MAX_LEN = 256


class LicenseActivate(BaseModel):
    license_key: str = Field(..., min_length=1, max_length=LICENSE_KEY_MAX_LEN)
    machine_id: str = Field(..., min_length=1, max_length=MACHINE_ID_MAX_LEN)



class LicenseValidate(BaseModel):
    license_key: str = Field(..., min_length=1, max_length=LICENSE_KEY_MAX_LEN)
    machine_id: str = Field(..., min_length=1, max_length=MACHINE_ID_MAX_LEN)


class LicenseDeactivate(BaseModel):
    license_key: str = Field(..., min_length=1, max_length=LICENSE_KEY_MAX_LEN)
    machine_id: str = Field(..., min_length=1, max_length=MACHINE_ID_MAX_LEN)


class LicenseRenew(BaseModel):
    license_key: str
    extra_days: int


class LicenseRevoke(BaseModel):
    license_key: str = Field(..., min_length=1, max_length=LICENSE_KEY_MAX_LEN)


class LicenseResponse(BaseModel):
    license_key: str
    expires_at: datetime
    is_active: bool


class LicenseInstall(BaseModel):
    license_blob: Any