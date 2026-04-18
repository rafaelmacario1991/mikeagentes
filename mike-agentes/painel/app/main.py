import time
import logging
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware

from app.auth.router import router as auth_router
from app.routers.dashboard import router as dashboard_router
from app.routers.agent import router as agent_router
from app.routers.professionals import router as professionals_router
from app.routers.services import router as services_router
from app.routers.availability import router as availability_router
from app.routers.appointments import router as appointments_router
from app.routers.admin import router as admin_router

logger = logging.getLogger("mike_agentes")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")

PUBLIC_PATHS = ["/login", "/static"]

# Rate limiting simples em memória: {ip: [timestamps]}
_login_attempts: dict[str, list[float]] = {}
_RATE_LIMIT_WINDOW = 60   # segundos
_RATE_LIMIT_MAX    = 10   # tentativas por janela


def _check_rate_limit(ip: str) -> bool:
    """Retorna True se dentro do limite, False se excedido."""
    now = time.time()
    attempts = [t for t in _login_attempts.get(ip, []) if now - t < _RATE_LIMIT_WINDOW]
    _login_attempts[ip] = attempts
    if len(attempts) >= _RATE_LIMIT_MAX:
        return False
    _login_attempts[ip].append(now)
    return True


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Rate limiting em POST /login
        if path == "/login" and request.method == "POST":
            ip = request.client.host if request.client else "unknown"
            if not _check_rate_limit(ip):
                logger.warning("Rate limit excedido para IP %s em /login", ip)
                return JSONResponse(
                    {"detail": "Muitas tentativas. Aguarde 1 minuto e tente novamente."},
                    status_code=429,
                )

        if any(path.startswith(p) for p in PUBLIC_PATHS):
            return await call_next(request)
        if not request.cookies.get("access_token"):
            return RedirectResponse(url="/login")
        response = await call_next(request)
        if response.status_code == 401:
            redirect = RedirectResponse(url="/login")
            redirect.delete_cookie("access_token")
            return redirect
        return response


app = FastAPI(title="Mike Agentes — Painel", docs_url=None, redoc_url=None)
app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(AuthMiddleware)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(agent_router)
app.include_router(professionals_router)
app.include_router(services_router)
app.include_router(availability_router)
app.include_router(appointments_router)
app.include_router(admin_router)


@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard")
