from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import get_current_user, get_effective_tenant, CurrentUser
from app.services.dashboard_service import get_dashboard_data

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user: CurrentUser = Depends(get_current_user)):
    tenant_id = get_effective_tenant(user, request)
    if not tenant_id:
        # Admin sem tenant selecionado → vai para lista de tenants
        return RedirectResponse(url="/admin/tenants", status_code=302)
    data = get_dashboard_data(tenant_id)
    return templates.TemplateResponse("dashboard/index.html", {
        "request": request,
        "user": user,
        **data,
    })
