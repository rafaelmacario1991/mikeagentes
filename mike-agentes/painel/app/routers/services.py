from fastapi import APIRouter, Request, Depends, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import get_current_user, get_effective_tenant, require_tenant, CurrentUser
from app.services import services_service, professionals_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/services", response_class=HTMLResponse)
async def list_services(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    professional_id: str | None = Query(None),
):
    tenant_id = require_tenant(user, request)
    all_services = services_service.list_services(tenant_id, professional_id)
    professionals = professionals_service.list_professionals(tenant_id)
    return templates.TemplateResponse("services/list.html", {
        "request": request,
        "user": user,
        "services": all_services,
        "professionals": professionals,
        "selected_professional": professional_id,
    })


@router.get("/services/new", response_class=HTMLResponse)
async def new_service_form(request: Request, user: CurrentUser = Depends(get_current_user)):
    tenant_id = require_tenant(user, request)
    professionals = professionals_service.list_professionals(tenant_id)
    return templates.TemplateResponse("services/form.html", {
        "request": request,
        "user": user,
        "service": None,
        "professionals": professionals,
    })


@router.post("/services/new")
async def create_service(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    name: str = Form(...),
    professional_id: str = Form(...),
    duration_minutes: int = Form(...),
    price: float = Form(...),
    description: str = Form(""),
):
    tenant_id = require_tenant(user, request)
    form_data = await request.form()
    payment_types = ", ".join(form_data.getlist("payment_types"))
    services_service.create_service(tenant_id, professional_id, name, duration_minutes, price, description, payment_types)
    return RedirectResponse(url="/services", status_code=302)


@router.get("/services/{service_id}/edit", response_class=HTMLResponse)
async def edit_service_form(
    service_id: str,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
):
    tenant_id = require_tenant(user, request)
    service = services_service.get_service(service_id, tenant_id)
    professionals = professionals_service.list_professionals(tenant_id)

    # Busca todos os profissionais que já têm esse serviço (mesmo nome)
    checked_pro_ids: list[str] = []
    if service:
        from app.services.supabase_client import get_admin_client
        client = get_admin_client()
        siblings = (
            client.table("services").select("professional_id")
            .eq("tenant_id", tenant_id)
            .eq("name", service["name"])
            .eq("ativo", True)
            .execute().data or []
        )
        checked_pro_ids = [s["professional_id"] for s in siblings]

    return templates.TemplateResponse("services/form.html", {
        "request": request,
        "user": user,
        "service": service,
        "professionals": professionals,
        "checked_pro_ids": checked_pro_ids,
    })


@router.post("/services/{service_id}/edit")
async def update_service(
    service_id: str,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    name: str = Form(...),
    duration_minutes: int = Form(...),
    price: float = Form(...),
    description: str = Form(""),
):
    tenant_id = require_tenant(user, request)
    form_data = await request.form()
    professional_ids = form_data.getlist("professional_id")
    payment_types = ", ".join(form_data.getlist("payment_types"))
    if not professional_ids:
        return RedirectResponse(url=f"/services/{service_id}/edit?error=1", status_code=302)
    services_service.sync_service_professionals(
        service_id, tenant_id, name, duration_minutes, price, professional_ids, description, payment_types
    )
    return RedirectResponse(url="/services", status_code=302)


@router.post("/services/{service_id}/toggle")
async def toggle_service(
    service_id: str,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    is_active: str = Form(...),
):
    tenant_id = require_tenant(user, request)
    services_service.toggle_service(service_id, tenant_id, is_active == "true")
    return RedirectResponse(url="/services", status_code=302)
