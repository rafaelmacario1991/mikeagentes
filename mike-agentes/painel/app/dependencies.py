from fastapi import Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from app.auth.service import get_user_from_token
from app.services.supabase_client import get_admin_client
from app.config import settings


class CurrentUser:
    def __init__(self, user_id: str, email: str, tenant_id: str | None, is_admin: bool):
        self.user_id = user_id
        self.email = email
        self.tenant_id = tenant_id
        self.is_admin = is_admin


async def get_current_user(request: Request) -> CurrentUser:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Não autenticado")

    try:
        payload = get_user_from_token(token)
    except Exception as e:
        import logging
        logging.getLogger("mike_agentes").error("get_user_from_token falhou: %s", e)
        raise HTTPException(status_code=401, detail="Token inválido")

    email = payload.get("email", "")
    user_id = payload.get("sub", "")
    is_admin = email.lower() == settings.ADMIN_EMAIL.lower()

    tenant_id = None
    if not is_admin:
        client = get_admin_client()
        result = client.table("tenants").select("id").eq("email", email).eq("ativo", True).limit(1).execute()
        if not result.data:
            raise HTTPException(status_code=403, detail="Acesso não autorizado para este email")
        tenant_id = result.data[0]["id"]

    return CurrentUser(user_id=user_id, email=email, tenant_id=tenant_id, is_admin=is_admin)


async def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Acesso restrito ao administrador")
    return user


def get_effective_tenant(user: CurrentUser, request: Request) -> str | None:
    """
    Admin pode impersonar qualquer tenant via cookie 'impersonate_tenant_id'.
    Tenant comum sempre usa o próprio tenant_id.
    Retorna None se admin não tiver impersonado nenhum tenant.
    """
    if user.is_admin:
        impersonate = request.cookies.get("impersonate_tenant_id")
        if impersonate:
            return impersonate
        return None
    return user.tenant_id


def require_tenant(user: CurrentUser, request: Request) -> str:
    """
    Igual a get_effective_tenant mas lança exceção 302 para /admin/tenants
    quando o admin não tiver impersonado nenhum tenant.
    """
    from fastapi.responses import RedirectResponse
    tenant_id = get_effective_tenant(user, request)
    if not tenant_id:
        raise HTTPException(status_code=307, detail="Selecione um tenant", headers={"Location": "/admin/tenants"})
    return tenant_id
