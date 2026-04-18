import logging
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import get_current_user, get_effective_tenant, CurrentUser
from app.services.dashboard_service import get_dashboard_data

logger = logging.getLogger("mike_agentes")

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    period: str = Query(default="week"),
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
):
    tenant_id = get_effective_tenant(user, request)
    if not tenant_id:
        return RedirectResponse(url="/admin/tenants", status_code=302)

    valid_periods = {"today", "tomorrow", "week", "next_week", "month", "custom"}
    if period not in valid_periods:
        period = "week"

    data = get_dashboard_data(tenant_id, period=period, start=start, end=end)
    logger.info("dashboard tenant=%s period=%s total=%s", tenant_id, period, data["total_today"])
    return templates.TemplateResponse("dashboard/index.html", {
        "request": request,
        "user": user,
        **data,
    })
