from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import get_current_user, require_tenant, CurrentUser
from app.services import agent_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/schedules", response_class=HTMLResponse)
async def schedules_page(request: Request, user: CurrentUser = Depends(get_current_user)):
    tenant_id = require_tenant(user, request)
    config = agent_service.get_agent_config(tenant_id) or {}
    return templates.TemplateResponse("schedules/index.html", {
        "request": request,
        "user": user,
        "config": config,
        "success": request.query_params.get("saved"),
    })


@router.post("/schedules")
async def schedules_save(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    reminder_24h: str = Form("false"),
    reminder_7d: str = Form("false"),
    reminder_14d: str = Form("false"),
):
    tenant_id = require_tenant(user, request)
    agent_service.upsert_agent_config(tenant_id, {
        "reminder_24h": reminder_24h == "true",
        "reminder_7d": reminder_7d == "true",
        "reminder_14d": reminder_14d == "true",
    })
    return RedirectResponse(url="/schedules?saved=1", status_code=302)
