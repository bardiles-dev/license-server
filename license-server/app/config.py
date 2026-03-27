import hashlib
import os
import socket

SESSION_TIMEOUT_MINUTES = 15
LICENSE_STATUS_ACTIVE = "active"
LICENSE_STATUS_EXPIRED = "expired"
LICENSE_STATUS_REVOKED = "revoked"


def get_server_machine_id_info() -> tuple[str, str]:
    """
    Devuelve (machine_id, source).
    source:
      - "env": definido por LICENSE_SERVER_MACHINE_ID (recomendado en contenedores)
      - "auto-hostname": derivado del hostname del runtime
    """
    configured = (os.getenv("LICENSE_SERVER_MACHINE_ID") or "").strip()
    if configured:
        return configured, "env"

    host = (socket.gethostname() or "unknown-host").strip()
    digest = hashlib.sha256(host.encode("utf-8")).hexdigest()[:24]
    return f"auto-{digest}", "auto-hostname"


def get_server_machine_id() -> str:
    machine_id, _ = get_server_machine_id_info()
    return machine_id
