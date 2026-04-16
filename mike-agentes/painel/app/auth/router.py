from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from app.auth.service import login_with_password
from app.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request, "error": None})


@router.post("/login")
async def login_post(request: Request, email: str = Form(...), password: str = Form(...)):
    try:
        access_token, _ = login_with_password(email, password)
    except Exception:
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Email ou senha incorretos."},
            status_code=401,
        )

    redirect = RedirectResponse(url="/dashboard", status_code=302)
    redirect.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=3600,
    )
    return redirect


@router.post("/logout")
async def logout():
    redirect = RedirectResponse(url="/login", status_code=302)
    redirect.delete_cookie("access_token")
    redirect.delete_cookie("impersonate_tenant_id")
    return redirect
