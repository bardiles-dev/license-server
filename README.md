# License Server & License Server Client

Este repositorio contiene dos componentes principales:

- **License Server**: Un servidor web para la gestión, validación e instalación de licencias de software, gestión de usuarios y visualización de sesiones activas.
- **License Server Client**: Un cliente sencillo para consumir y verificar licencias contra el License Server desde otras aplicaciones (por ejemplo, apps de escritorio).

---

## License Server

### **Características principales**

- Gestión y validación de licencias (incluyendo soporte para diferentes tipos y bloqueos por máquina).
- Panel de administración con autenticación, gestión de roles y usuarios.
- Visualización y administración de licencias instaladas y sesiones activas.
- Instalación sencilla de licencias mediante clave.
- Protección contra ataques comunes:
  - XSS: Escapado automático de Jinja2, CSP y validaciones de entrada.
  - SQL Injection: Uso de ORM, sin SQL crudo en endpoints críticos.
  - Open Redirect: Redirecciones seguras sólo a URLs permitidas o constantes.
  - DoS/payload grande: Límite en longitud de campos y strings de instalación.
  - Clickjacking: X-Frame-Options y CSP restrictivo.
  - CSRF: Implementado por token + cookie.
- Código base en Python (Flask), HTML5, Bootstrap 5.

### **Prerrequisitos**

- Python 3.8+
- Dependencias (ver requirements.txt)
- Base de datos (SQLite por defecto, soporta también otras vía SQLAlchemy)

### **Instalación rápida**

1. Clona el repo:
    ```sh
    git clone <REPO_URL>
    cd license-server
    ```
2. Instala las dependencias:
    ```sh
    pip install -r requirements.txt
    ```
3. (Opcional) Ajusta la configuración en `app/config.py`
4. Inicia el servidor:
    ```sh
    python run.py
    ```
5. Accede a `http://localhost:PORT` en tu navegador.

### **Estructura de carpetas relevante**

- `app/`
  - `models.py` &mdash; Modelos SQLAlchemy de usuarios, licencias, sesiones, roles.
  - `routes/` &mdash; Rutas Flask (`users`, `license`, admin).
  - `templates/` &mdash; Plantillas HTML/Jinja2.
  - `config.py` &mdash; Parámetros clave (tiempos, constantes de licencia).
- `run.py` &mdash; Entrada para ejecutar el servidor.

---

## License Server Client

> **Nota:** El cliente puede estar en otra carpeta como `license-server-client/` o similar.

- Permite conectarse a una instancia de License Server y validar licencias desde aplicaciones externas.
- Uso típico: se importa como módulo en la app a proteger y hace peticiones HTTP para validar la licencia del usuario final.

### **Uso básico**

```python
from license_server_client import LicenseClient

client = LicenseClient(server_url="http://<server-host>:<port>", api_key="...")
is_valid = client.verify_license(license_key="AAA-123-BBB", machine_id="DEADBEEF")
if is_valid:
    # Grant access
else:
    # Bloquear acceso
```

Consultar el README específico del cliente si existe para detalles de inicialización y manejo de respuestas.

---

## Seguridad

Resumen de mitigaciones incluidas:
- **XSS**: CSP fuerte, escapado por defecto.
- **SQL Injection:** Uso estricto del ORM, sin SQL manual.
- **Open Redirect:** Solo redirecciones a destinos fijos.
- **DoS/Abuso:** Límite de campo y payload.
- **Clickjacking:** X-Frame-Options, policy de frame.
- **CSRF:** Token en todas las acciones POST de administración.
- **Rate Limiting:** (Opcional, se recomienda agregar para endpoints sensibles, como login).

---

## Licencia

MIT © [Autor(s)]



# Resumen rápido / seguridad
Riesgo	Mitigación
XSS	CSP, allowlist de ?error=, Jinja2 con escape por defecto, longitudes en schemas.
SQL injection	Uso de ORM con parámetros; sin SQL crudo en las rutas tocadas.
Open redirect	Redirecciones con URLs fijas (constantes).
DoS / payload grande	Límite de longitud del string de instalación y de campos en schemas.
Clickjacking	X-Frame-Options y CSP frame-ancestors 'none'.
CSRF	Ya existía (cookie + form token); no se ha quitado.
Si quieres, el siguiente paso puede ser añadir rate limiting en login y en los endpoints de licencias o endurecer aún más la CSP.