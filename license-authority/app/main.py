from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .database import engine, get_db, SessionLocal
from .models import Base, User
from .routes import auth_routes, license_routes, web
from .security.middleware import SecurityHeadersMiddleware
from .security.auth import hash_password

# ---------------------------
# INIT
# ---------------------------
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="License Authority v2",
    swagger_ui_parameters={
        "tryItOutEnabled": True,
        "persistAuthorization": True,
        "displayRequestDuration": True,
    },
)
app.add_middleware(SecurityHeadersMiddleware)


def _should_return_json_401(request: Request) -> bool:
    """True si ante 401 devolver JSON (no redirect). Rutas API y peticiones desde /docs."""
    path = request.scope.get("path") or ""
    if not path and getattr(request, "url", None):
        path = getattr(request.url, "path", "") or ""
    path_lower = (path or "").strip().lower()
    if "/create" in path_lower or path_lower.startswith("/renew") or path_lower.startswith("/revoke"):
        return True
    if path_lower == "/licenses" or path_lower.startswith("/openapi"):
        return True
    referer = (request.headers.get("referer") or "").lower()
    if "/docs" in referer or "/redoc" in referer:
        return True
    accept = (request.headers.get("accept") or "").lower()
    # Solo si piden explícitamente JSON y no HTML (navegador a / envía text/html y */* → redirect)
    if "application/json" in accept and "text/html" not in accept:
        return True
    return False


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code != 401:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    if _should_return_json_401(request):
        return JSONResponse(status_code=401, content={"detail": exc.detail or "Unauthorized"})
    return RedirectResponse(url="/login", status_code=302)


# ---------------------------
# Static y rutas
# ---------------------------
_app_dir = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(_app_dir / "static")), name="static")
app.include_router(auth_routes.router)
app.include_router(web.router)
app.include_router(license_routes.router)


@app.on_event("startup")
def create_default_user():
    """Crea usuario admin/admin si no existe ningún usuario (como en license-server)."""
    db = SessionLocal()
    try:
        if db.query(User).first() is None:
            user = User(
                username="admin",
                password_hash=hash_password("admin"),
                is_active=True,
            )
            db.add(user)
            db.commit()
    finally:
        db.close()
