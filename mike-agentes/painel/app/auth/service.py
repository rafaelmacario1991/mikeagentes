import jwt
from app.services.supabase_client import get_anon_client
from app.config import settings


def login_with_password(email: str, password: str) -> tuple[str, str]:
    """
    Autentica via Supabase Auth.
    Retorna (access_token, refresh_token).
    Lança Exception se credenciais inválidas.
    """
    client = get_anon_client()
    response = client.auth.sign_in_with_password({"email": email, "password": password})
    return response.session.access_token, response.session.refresh_token


def get_user_from_token(token: str) -> dict:
    """
    Valida o token via Supabase Auth API.
    Compatível com ES256 e HS256 — independente do algoritmo do JWT.
    Lança Exception se token inválido ou expirado.
    """
    client = get_anon_client()
    response = client.auth.get_user(token)

    if not response or not response.user:
        raise ValueError("Token inválido")

    user = response.user
    sub = str(user.id) if user.id else ""
    email = user.email or ""

    if not sub:
        raise ValueError("Token sem sub")

    return {"sub": sub, "email": email}
