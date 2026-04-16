from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.auth.router import router as auth_router
from app.routers.dashboard import router as dashboard_router
from app.routers.agent import router as agent_router
from app.routers.professionals import router as professionals_router
from app.routers.services import router as services_router
from app.routers.availability import router as availability_router
from app.routers.appointments import router as appointments_router
from app.routers.admin import router as admin_router

PUBLIC_PATHS = ["/login", "/static"]


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path.startswith(p) for p in PUBLIC_PATHS):
            return await call_next(request)
        if not request.cookies.get("access_token"):
            return RedirectResponse(url="/login")
        response = await call_next(request)
        # Se retornou 401, redireciona para login (token expirado/inválido)
        if response.status_code == 401:
            redirect = RedirectResponse(url="/login")
            redirect.delete_cookie("access_token")
            return redirect
        return response


app = FastAPI(title="Mike Agentes — Painel")
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


@app.get("/debug-token")
async def debug_token(request: Request):
    """Rota temporária para diagnóstico — remover após resolver."""
    import base64, json
    token = request.cookies.get("access_token", "")
    result = {"token_present": bool(token), "token_length": len(token)}
    if token:
        try:
            parts = token.split(".")
            result["parts_count"] = len(parts)
            if len(parts) == 3:
                p = parts[1]
                p += "=" * (4 - len(p) % 4)
                payload = json.loads(base64.urlsafe_b64decode(p))
                result["payload"] = payload
        except Exception as e:
            result["decode_error"] = str(e)
    return result
