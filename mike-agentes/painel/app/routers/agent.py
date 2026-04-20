from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import get_current_user, get_effective_tenant, require_tenant, CurrentUser
from app.services import agent_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/agent/config", response_class=HTMLResponse)
async def agent_config_page(request: Request, user: CurrentUser = Depends(get_current_user)):
    tenant_id = require_tenant(user, request)
    config = agent_service.get_agent_config(tenant_id) or {}
    return templates.TemplateResponse("agent/config.html", {
        "request": request,
        "user": user,
        "config": config,
        "success": request.query_params.get("saved"),
    })


@router.post("/agent/config")
async def agent_config_save(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    agent_name: str = Form(...),
    welcome_message: str = Form(""),
    agent_persona: str = Form(...),
    slot_duration_min: int = Form(30),
    max_advance_days: int = Form(14),
):
    tenant_id = require_tenant(user, request)
    agent_service.upsert_agent_config(tenant_id, {
        "agent_name": agent_name,
        "welcome_message": welcome_message or None,
        "agent_persona": agent_persona,
        "slot_duration_min": slot_duration_min,
        "max_advance_days": max_advance_days,
    })
    return RedirectResponse(url="/agent/config?saved=1", status_code=302)


@router.post("/agent/toggle")
async def agent_toggle(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    is_active: str = Form(...),
):
    tenant_id = require_tenant(user, request)
    agent_service.toggle_agent(tenant_id, is_active == "true")
    return RedirectResponse(url="/agent/config", status_code=302)
