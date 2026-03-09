"""
Reexporta la codificación de licencia a string desde license_routes.
El string es la "contraseña" que se pasa al cliente; license-server lo descifra
con decode_payload (security.py) y usa /install-from-string (license.py).
"""
from .routes.license_routes import encode_license_to_string

__all__ = ["encode_license_to_string"]
