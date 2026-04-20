import logging
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import require_admin, CurrentUser
from app.services import admin_service, agent_service

logger = logging.getLogger("mike_agentes")

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/admin/tenants", response_class=HTMLResponse)
async def list_tenants(request: Request, user: CurrentUser = Depends(require_admin)):
    tenants = admin_service.list_tenants()
    return templates.TemplateResponse("admin/tenants.html", {
        "request": request,
        "user": user,
        "tenants": tenants,
        "impersonating": request.cookies.get("impersonate_tenant_id"),
    })


@router.get("/admin/tenants/new", response_class=HTMLResponse)
async def new_tenant_page(request: Request, user: CurrentUser = Depends(require_admin)):
    return templates.TemplateResponse("admin/tenant_new.html", {
        "request": request,
        "user": user,
        "error": None,
    })


@router.post("/admin/tenants/new")
async def create_tenant_post(
    request: Request,
    user: CurrentUser = Depends(require_admin),
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    plan: str = Form("starter"),
):
    error = admin_service.create_tenant(name=name, email=email, password=password, plan=plan)
    if error:
        return templates.TemplateResponse("admin/tenant_new.html", {
            "request": request,
            "user": user,
            "error": error,
        }, status_code=400)
    return RedirectResponse(url="/admin/tenants", status_code=302)


@router.post("/admin/tenants/{tenant_id}/toggle")
async def toggle_tenant(
    tenant_id: str,
    user: CurrentUser = Depends(require_admin),
    is_active: str = Form(...),
):
    admin_service.toggle_tenant(tenant_id, is_active == "true")
    return RedirectResponse(url="/admin/tenants", status_code=302)


_IMPERSONATE_TTL = 3600  # 1 hora


@router.get("/admin/tenants/{tenant_id}/agent", response_class=HTMLResponse)
async def admin_agent_config_page(tenant_id: str, request: Request, user: CurrentUser = Depends(require_admin)):
    tenant = admin_service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    config = agent_service.get_agent_config(tenant_id) or {}
    return templates.TemplateResponse("admin/agent_config.html", {
        "request": request,
        "user": user,
        "tenant": tenant,
        "config": config,
        "success": request.query_params.get("saved"),
    })


@router.post("/admin/tenants/{tenant_id}/agent")
async def admin_agent_config_save(
    tenant_id: str,
    request: Request,
    user: CurrentUser = Depends(require_admin),
    whatsapp_instance: str = Form(...),
    mkpro_instance_id: str = Form(""),
    mkpro_token: str = Form(""),
    redis_prefix: str = Form(""),
    ativo: str = Form("false"),
):
    agent_service.upsert_agent_config(tenant_id, {
        "whatsapp_instance": whatsapp_instance,
        "mkpro_instance_id": mkpro_instance_id or None,
        "mkpro_token": mkpro_token or None,
        "redis_prefix": redis_prefix or None,
        "ativo": ativo == "true",
    })
    return RedirectResponse(url=f"/admin/tenants/{tenant_id}/agent?saved=1", status_code=302)


@router.get("/admin/switch/{tenant_id}")
async def switch_tenant(tenant_id: str, user: CurrentUser = Depends(require_admin)):
    """Admin assume contexto de um tenant específico."""
    tenant = admin_service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    tenant_name = tenant["name"]
    logger.info("admin=%s impersonando tenant=%s (%s)", user.email, tenant_id, tenant_name)
    redirect = RedirectResponse(url="/dashboard", status_code=302)
    redirect.set_cookie(
        key="impersonate_tenant_id",
        value=tenant_id,
        httponly=True,
        samesite="lax",
        max_age=_IMPERSONATE_TTL,
    )
    redirect.set_cookie(
        key="impersonate_tenant_name",
        value=tenant_name,
        httponly=False,
        samesite="lax",
        max_age=_IMPERSONATE_TTL,
    )
    return redirect


@router.get("/admin/switch-exit")
async def switch_exit(user: CurrentUser = Depends(require_admin)):
    """Admin sai da impersonação."""
    redirect = RedirectResponse(url="/admin/tenants", status_code=302)
    redirect.delete_cookie("impersonate_tenant_id")
    redirect.delete_cookie("impersonate_tenant_name")
    return redirect
