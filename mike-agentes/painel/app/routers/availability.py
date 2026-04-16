import json
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import get_current_user, get_effective_tenant, CurrentUser
from app.services import availability_service, professionals_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

DAYS = ["Domingo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]


@router.get("/availability", response_class=HTMLResponse)
async def availability_page(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    professional_id: str | None = Query(None),
):
    tenant_id = get_effective_tenant(user, request)
    professionals = professionals_service.list_professionals(tenant_id)

    slots = {}
    if professional_id:
        slots = availability_service.get_week_availability(tenant_id, professional_id)

    # Monta lista de 7 dias para o template Alpine.js
    week = []
    for i, day_name in enumerate(DAYS):
        row = slots.get(i, {})
        week.append({
            "index": i,
            "name": day_name,
            "active": row.get("ativo", False),
            "start": str(row.get("start_time", "08:00"))[:5],
            "end": str(row.get("end_time", "18:00"))[:5],
        })

    return templates.TemplateResponse("availability/week_grid.html", {
        "request": request,
        "user": user,
        "professionals": professionals,
        "selected_professional": professional_id,
        "week_json": json.dumps(week),
    })


@router.post("/availability")
async def save_availability(request: Request, user: CurrentUser = Depends(get_current_user)):
    tenant_id = get_effective_tenant(user, request)
    body = await request.json()
    professional_id = body.get("professional_id")
    days = body.get("days", [])

    if not professional_id:
        return JSONResponse({"error": "professional_id obrigatório"}, status_code=400)

    availability_service.save_week_availability(tenant_id, professional_id, days)
    return JSONResponse({"ok": True})
