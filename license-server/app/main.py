from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from .database import Base, engine
from .routes import web, auth, admin, license, users
from .core.startup import init_app
from .security.middleware import SecurityHeadersMiddleware

app = FastAPI(
    swagger_ui_parameters={
        "tryItOutEnabled": True,
        "persistAuthorization": True,
        "displayRequestDuration": True,
    }
)

# Cabeceras de seguridad (XSS, clickjacking, CSP, etc.)
app.add_middleware(SecurityHeadersMiddleware)

# Templates y static
app.mount("/static", StaticFiles(directory="app/static"), name="static")

Base.metadata.create_all(bind=engine)

# Registrar routers
app.include_router(web.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(license.router)
app.include_router(users.router)

def _should_return_json_401(request: Request) -> bool:
    """True si ante 401 devolver JSON (no redirect). Rutas API y peticiones desde /docs."""
    path = request.scope.get("path") or ""
    if not path and getattr(request, "url", None):
        path = getattr(request.url, "path", "") or ""
    path_lower = (path or "").strip().lower()
    if "/api" in path_lower or (path_lower and path_lower.startswith("/openapi")):
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
async def auth_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        if _should_return_json_401(request):
            return JSONResponse(status_code=401, content={"detail": exc.detail or "Unauthorized"})
        return RedirectResponse("/login", status_code=302)
    if exc.status_code == 403 and not _should_return_json_401(request):
        return RedirectResponse("/dashboard?forbidden=1", status_code=302)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
    
# Startup
init_app(app)



