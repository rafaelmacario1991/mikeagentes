from fastapi import APIRouter, Request, Depends, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import get_current_user, get_effective_tenant, require_tenant, CurrentUser
from app.services import appointments_service, professionals_service, services_service
from datetime import date, timedelta
from collections import defaultdict

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
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    status: str | None = Query(default=None),
):
    tenant_id = require_tenant(user, request)

    today = date.today()
    date_from = start or today.isoformat()
    date_to   = end   or (today + timedelta(days=7)).isoformat()

    # Garante ordem correta
    if date_from > date_to:
        date_from, date_to = date_to, date_from

    appointments = appointments_service.list_appointments(tenant_id, date_from, date_to, status)

    # Agrupa por data para exibição multi-dia
    multi_day = date_from != date_to
    grouped_map: dict[str, list] = defaultdict(list)
    for apt in appointments:
        day = apt.get("display_date") or (apt["scheduled_at"][:10] if apt.get("scheduled_at") else "—")
        grouped_map[day].append(apt)
    appointments_grouped = [
        {"date": d, "rows": grouped_map[d]}
        for d in sorted(grouped_map.keys())
    ]

    # Label do período
    if date_from == date_to:
        period_label = date.fromisoformat(date_from).strftime("%d/%m/%Y")
    else:
        period_label = (
            f"{date.fromisoformat(date_from).strftime('%d/%m/%Y')} — "
            f"{date.fromisoformat(date_to).strftime('%d/%m/%Y')}"
        )

    return templates.TemplateResponse("appointments/list.html", {
        "request": request,
        "user": user,
        "appointments": appointments,
        "appointments_grouped": appointments_grouped,
        "multi_day": multi_day,
        "date_from": date_from,
        "date_to": date_to,
        "status_filter": status,
        "status_labels": STATUS_LABELS,
        "period_label": period_label,
    })


@router.post("/appointments/{appointment_id}/confirm")
async def confirm_appointment(
    appointment_id: str,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
):
    tenant_id = require_tenant(user, request)
    appointments_service.update_appointment_status(appointment_id, tenant_id, "confirmed")
    qs = _build_qs(start, end)
    return RedirectResponse(url=f"/appointments{qs}", status_code=302)


@router.post("/appointments/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: str,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
):
    tenant_id = require_tenant(user, request)
    appointments_service.update_appointment_status(appointment_id, tenant_id, "cancelled")
    qs = _build_qs(start, end)
    return RedirectResponse(url=f"/appointments{qs}", status_code=302)


# ── Novo agendamento manual ───────────────────────────────────────────────────

@router.get("/appointments/new", response_class=HTMLResponse)
async def new_appointment_form(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
):
    tenant_id = require_tenant(user, request)
    professionals = professionals_service.list_professionals(tenant_id)
    # Só profissionais ativos
    professionals = [p for p in professionals if p.get("ativo", True)]
    return templates.TemplateResponse("appointments/new.html", {
        "request": request,
        "user": user,
        "professionals": professionals,
        "today": date.today().isoformat(),
    })


@router.post("/appointments/new")
async def create_appointment(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    professional_id: str = Form(...),
    service_id: str = Form(...),
    apt_date: str = Form(...),
    apt_time: str = Form(...),
    client_phone: str = Form(...),
    client_name: str = Form(""),
    notes: str = Form(""),
):
    tenant_id = require_tenant(user, request)

    # Busca ou cria o serviço para pegar duration_min
    svc = services_service.get_service(service_id, tenant_id)
    if not svc:
        return RedirectResponse(url="/appointments/new?error=servico_invalido", status_code=302)

    duration_min = svc.get("duration_min", 30)

    # Exige nome real do cliente
    name = client_name.strip()
    if not name:
        return RedirectResponse(url="/appointments/new?error=nome_obrigatorio", status_code=302)
    client_id = appointments_service.get_or_create_client(tenant_id, name, client_phone)

    appointments_service.create_appointment_manual(
        tenant_id=tenant_id,
        client_id=client_id,
        professional_id=professional_id,
        service_id=service_id,
        date_str=apt_date,
        time_str=apt_time,
        duration_min=duration_min,
        notes=notes.strip() or None,
    )

    return RedirectResponse(
        url=f"/appointments?start={apt_date}&end={apt_date}",
        status_code=302,
    )


# ── APIs AJAX ─────────────────────────────────────────────────────────────────

@router.get("/appointments/api/services")
async def api_services(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    professional_id: str = Query(...),
):
    tenant_id = require_tenant(user, request)
    from app.services.supabase_client import get_admin_client
    client = get_admin_client()
    result = (
        client.table("services")
        .select("id, name, duration_min, price")
        .eq("tenant_id", tenant_id)
        .eq("professional_id", professional_id)
        .eq("ativo", True)
        .order("name")
        .execute()
    )
    return JSONResponse(result.data or [])


@router.get("/appointments/api/slots")
async def api_slots(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    professional_id: str = Query(...),
    apt_date: str = Query(...),
):
    tenant_id = require_tenant(user, request)
    slots = appointments_service.get_available_slots(tenant_id, professional_id, apt_date)
    return JSONResponse(slots)


@router.get("/appointments/api/clients/search")
async def api_clients_search(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    q: str = Query(default=""),
):
    tenant_id = require_tenant(user, request)
    clients = appointments_service.search_clients(tenant_id, q)
    return JSONResponse(clients)


# ─────────────────────────────────────────────────────────────────────────────

def _build_qs(start: str | None, end: str | None) -> str:
    params = []
    if start:
        params.append(f"start={start}")
    if end:
        params.append(f"end={end}")
    return ("?" + "&".join(params)) if params else ""
