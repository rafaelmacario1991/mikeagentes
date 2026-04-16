from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import require_admin, CurrentUser
from app.services import admin_service

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


@router.post("/admin/tenants/{tenant_id}/toggle")
async def toggle_tenant(
    tenant_id: str,
    user: CurrentUser = Depends(require_admin),
    is_active: str = Form(...),
):
    admin_service.toggle_tenant(tenant_id, is_active == "true")
    return RedirectResponse(url="/admin/tenants", status_code=302)


@router.get("/admin/switch/{tenant_id}")
async def switch_tenant(tenant_id: str, user: CurrentUser = Depends(require_admin)):
    """Admin assume contexto de um tenant específico."""
    redirect = RedirectResponse(url="/dashboard", status_code=302)
    redirect.set_cookie(
        key="impersonate_tenant_id",
        value=tenant_id,
        httponly=True,
        samesite="lax",
    )
    return redirect


@router.get("/admin/switch-exit")
async def switch_exit(user: CurrentUser = Depends(require_admin)):
    """Admin sai da impersonação."""
    redirect = RedirectResponse(url="/admin/tenants", status_code=302)
    redirect.delete_cookie("impersonate_tenant_id")
    return redirect
