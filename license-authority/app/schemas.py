from pydantic import BaseModel, model_validator, ConfigDict, Field
from typing import Optional, List
from enum import Enum


class LicenseType(str, Enum):
    machine = "machine"
    floating = "floating"


# Límites para evitar XSS, inyección y payloads enormes
COMPANY_MAX_LEN = 200
MACHINE_LOCK_MAX_LEN = 256
FEATURE_ID_MAX_LEN = 64
FEATURE_VERSION_MAX_LEN = 32
FEATURE_FUNCIONALITY_MAX_LEN = 128
DURATION_DAYS_MAX = 3650
MAX_ACTIVATIONS_MAX = 1000


class FeatureItem(BaseModel):
    """Una herramienta/módulo dentro de la licencia. `id` es el identificador (ej: ia-agent, audit)."""
    model_config = ConfigDict(extra="allow")
    id: str = Field(..., min_length=1, max_length=FEATURE_ID_MAX_LEN)
    version: Optional[str] = Field(None, max_length=FEATURE_VERSION_MAX_LEN)
    funcionality: Optional[str] = Field(None, max_length=FEATURE_FUNCIONALITY_MAX_LEN)


class LicenseCreate(BaseModel):
    company: str = Field(..., min_length=1, max_length=COMPANY_MAX_LEN)
    license_type: LicenseType
    max_activations: int = Field(1, ge=1, le=MAX_ACTIVATIONS_MAX)
    machine_lock: Optional[str] = Field(
        default=None,
        max_length=MACHINE_LOCK_MAX_LEN,
        description="Requerido si license_type=machine: fingerprint/hash de la máquina (ej. SHA256 de hostname+mac). "
        "El cliente envía este mismo valor como machine_id al activar; license-server comprueba machine_id == machine_lock. "
        "Debe ser null o omitir si license_type=floating.",
    )
    duration_days: int = Field(..., ge=1, le=DURATION_DAYS_MAX)
    features: Optional[List[FeatureItem]] = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "company": "MiEmpresa",
                    "license_type": "machine",
                    "max_activations": 1,
                    "machine_lock": "a1b2c3d4e5f6-sha256-fingerprint-de-la-maquina",
                    "duration_days": 365,
                    "features": [{"id": "ia-agent", "version": "2026.1", "funcionality": "HU,EXEC,QA-AGENT"}],
                },
                {
                    "company": "MiEmpresa",
                    "license_type": "floating",
                    "max_activations": 5,
                    "duration_days": 365,
                    "features": [
                        {"id": "ia-agent", "version": "2026.1", "funcionality": "HU,EXEC,QA-AGENT"},
                        {"id": "audit", "version": "2025.1"},
                    ],
                },
            ]
        }
    )

    @model_validator(mode="after")
    def validate_logic(self):

        if self.license_type == LicenseType.machine and not self.machine_lock:
            raise ValueError("machine_lock is required for machine licenses")

        if self.license_type == LicenseType.floating and self.machine_lock:
            raise ValueError("machine_lock must be null for floating licenses")

        if self.license_type == LicenseType.machine and self.max_activations != 1:
            raise ValueError("machine licenses must have max_activations = 1")

        return self


class LicenseRenew(BaseModel):
    extra_days: int = Field(..., ge=1, le=DURATION_DAYS_MAX)
