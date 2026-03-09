"""
Validación y saneamiento de entradas para prevenir XSS, inyección y valores inválidos.
"""
import re
from typing import Optional

# Límites razonables
USERNAME_MIN_LEN = 2
USERNAME_MAX_LEN = 64
EMAIL_MAX_LEN = 254
PASSWORD_MIN_LEN = 8
PASSWORD_MAX_LEN = 256
LICENSE_STRING_MAX_LEN = 100_000
LICENSE_KEY_MAX_LEN = 64
MACHINE_ID_MAX_LEN = 256

# Solo alfanuméricos y guión bajo para usuario
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")
# Email básico (evitar inyección en campos de correo)
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

# Valores permitidos para query param ?error= (evitar XSS reflejado)
ALLOWED_INSTALL_ERRORS = frozenset({"csrf", "empty", "decode", "signature"})


def allowlist_install_error(value: Optional[str]) -> Optional[str]:
    """Devuelve value solo si está en la lista permitida; si no, None."""
    if value is None or not value.strip():
        return None
    v = value.strip().lower()
    return v if v in ALLOWED_INSTALL_ERRORS else None


def validate_username(username: str) -> tuple[bool, str]:
    """
    Valida nombre de usuario: longitud y caracteres permitidos.
    Devuelve (ok, mensaje_error).
    """
    s = username.strip()
    if len(s) < USERNAME_MIN_LEN:
        return False, f"El usuario debe tener al menos {USERNAME_MIN_LEN} caracteres."
    if len(s) > USERNAME_MAX_LEN:
        return False, f"El usuario no puede superar {USERNAME_MAX_LEN} caracteres."
    if not USERNAME_PATTERN.match(s):
        return False, "El usuario solo puede contener letras, números y guión bajo."
    return True, ""


def validate_email(email: str) -> tuple[bool, str]:
    """Valida formato y longitud de email."""
    s = email.strip().lower()
    if not s:
        return False, "El email no puede estar vacío."
    if len(s) > EMAIL_MAX_LEN:
        return False, f"El email no puede superar {EMAIL_MAX_LEN} caracteres."
    if not EMAIL_PATTERN.match(s):
        return False, "Formato de email inválido."
    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    """Longitud mínima/máxima de contraseña."""
    if len(password) < PASSWORD_MIN_LEN:
        return False, f"La contraseña debe tener al menos {PASSWORD_MIN_LEN} caracteres."
    if len(password) > PASSWORD_MAX_LEN:
        return False, f"La contraseña no puede superar {PASSWORD_MAX_LEN} caracteres."
    return True, ""


def sanitize_license_install_string(raw: str) -> Optional[str]:
    """
    Recorta y limita longitud del string de instalación.
    Devuelve None si está vacío o supera el límite (evitar DoS por payload enorme).
    """
    s = raw.strip()
    if not s:
        return None
    if len(s) > LICENSE_STRING_MAX_LEN:
        return None
    return s
