from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import get_current_user, require_tenant, CurrentUser
from app.services.supabase_client import get_admin_client

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _get_tenant(tenant_id: str) -> dict:
    client = get_admin_client()
    result = client.table("tenants").select("*").eq("id", tenant_id).limit(1).execute()
    return result.data[0] if result.data else {}


def _update_tenant(tenant_id: str, data: dict) -> None:
    client = get_admin_client()
    client.table("tenants").update(data).eq("id", tenant_id).execute()


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, user: CurrentUser = Depends(get_current_user)):
    tenant_id = require_tenant(user, request)
    tenant = _get_tenant(tenant_id)
    return templates.TemplateResponse("profile/index.html", {
        "request": request,
        "user": user,
        "tenant": tenant,
        "success": request.query_params.get("saved"),
    })


@router.post("/profile")
async def profile_save(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    name: str = Form(...),
    phone: str = Form(""),
    city: str = Form(""),
    address: str = Form(""),
    description: str = Form(""),
):
    tenant_id = require_tenant(user, request)
    _update_tenant(tenant_id, {
        "name": name,
        "phone": phone or None,
        "city": city or None,
        "address": address or None,
        "description": description or None,
    })
    return RedirectResponse(url="/profile?saved=1", status_code=302)
