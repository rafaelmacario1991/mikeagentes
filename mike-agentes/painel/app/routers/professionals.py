from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import get_current_user, get_effective_tenant, require_tenant, CurrentUser
from app.services import professionals_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/professionals", response_class=HTMLResponse)
async def list_professionals(request: Request, user: CurrentUser = Depends(get_current_user)):
    tenant_id = require_tenant(user, request)
    professionals = professionals_service.list_professionals(tenant_id)
    return templates.TemplateResponse("professionals/list.html", {
        "request": request,
        "user": user,
        "professionals": professionals,
    })


@router.get("/professionals/new", response_class=HTMLResponse)
async def new_professional_form(request: Request, user: CurrentUser = Depends(get_current_user)):
    return templates.TemplateResponse("professionals/form.html", {
        "request": request,
        "user": user,
        "professional": None,
    })


@router.post("/professionals/new")
async def create_professional(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    name: str = Form(...),
    specialty: str = Form(""),
    bio: str = Form(""),
    photo_url: str = Form(""),
):
    tenant_id = require_tenant(user, request)
    professionals_service.create_professional(tenant_id, name, specialty, bio, photo_url)
    return RedirectResponse(url="/professionals", status_code=302)


@router.get("/professionals/{professional_id}/edit", response_class=HTMLResponse)
async def edit_professional_form(
    professional_id: str,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
):
    tenant_id = require_tenant(user, request)
    professional = professionals_service.get_professional(professional_id, tenant_id)
    return templates.TemplateResponse("professionals/form.html", {
        "request": request,
        "user": user,
        "professional": professional,
    })


@router.post("/professionals/{professional_id}/edit")
async def update_professional(
    professional_id: str,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    name: str = Form(...),
    specialty: str = Form(""),
    bio: str = Form(""),
    photo_url: str = Form(""),
):
    tenant_id = require_tenant(user, request)
    professionals_service.update_professional(professional_id, tenant_id, name, specialty, bio, photo_url)
    return RedirectResponse(url="/professionals", status_code=302)


@router.post("/professionals/{professional_id}/toggle")
async def toggle_professional(
    professional_id: str,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    is_active: str = Form(...),
):
    tenant_id = require_tenant(user, request)
    professionals_service.toggle_professional(professional_id, tenant_id, is_active == "true")
    return RedirectResponse(url="/professionals", status_code=302)
