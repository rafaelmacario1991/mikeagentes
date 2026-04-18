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
    Valida assinatura do JWT Supabase e extrai 'sub' (user_id) e 'email'.
    Lança jwt.InvalidTokenError em caso de token inválido ou expirado.
    """
    payload = jwt.decode(
        token,
        settings.SUPABASE_JWT_SECRET,
        algorithms=["HS256"],
        audience="authenticated",
        options={"verify_exp": True},
    )

    sub = payload.get("sub") or ""
    email = payload.get("email") or ""

    if not sub:
        raise ValueError("Token sem sub")

    return {"sub": sub, "email": email}
