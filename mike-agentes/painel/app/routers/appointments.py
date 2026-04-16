from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import get_current_user, get_effective_tenant, CurrentUser
from app.services import appointments_service
from datetime import date

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

STATUS_LABELS = {
    "scheduled": "Agendado",
    "confirmed": "Confirmado",
    "cancelled": "Cancelado",
    "completed": "Concluído",
    "no_show": "Não compareceu",
}


@router.get("/appointments", response_class=HTMLResponse)
async def list_appointments(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    date_filter: str | None = Query(None, alias="date"),
    status: str | None = Query(None),
):
    tenant_id = get_effective_tenant(user, request)
    if not date_filter:
        date_filter = date.today().isoformat()

    appointments = appointments_service.list_appointments(tenant_id, date_filter, status)
    return templates.TemplateResponse("appointments/list.html", {
        "request": request,
        "user": user,
        "appointments": appointments,
        "date_filter": date_filter,
        "status_filter": status,
        "status_labels": STATUS_LABELS,
    })


@router.post("/appointments/{appointment_id}/confirm")
async def confirm_appointment(
    appointment_id: str,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
):
    tenant_id = get_effective_tenant(user, request)
    appointments_service.update_appointment_status(appointment_id, tenant_id, "confirmed")
    return RedirectResponse(url="/appointments", status_code=302)


@router.post("/appointments/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: str,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
):
    tenant_id = get_effective_tenant(user, request)
    appointments_service.update_appointment_status(appointment_id, tenant_id, "cancelled")
    return RedirectResponse(url="/appointments", status_code=302)
