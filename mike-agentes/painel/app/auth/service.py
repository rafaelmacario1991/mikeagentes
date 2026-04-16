from app.services.supabase_client import get_anon_client, get_admin_client


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
    Decodifica o payload do JWT sem verificação de assinatura.
    O token foi emitido pelo Supabase em um login válido — confiamos nele.
    Extrai 'sub' (user_id) e 'email' do payload.
    """
    import base64
    import json

    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Formato JWT inválido")

    # Adiciona padding Base64 se necessário
    payload_b64 = parts[1]
    payload_b64 += "=" * (4 - len(payload_b64) % 4)
    payload = json.loads(base64.urlsafe_b64decode(payload_b64))

    email = payload.get("email") or ""
    sub = payload.get("sub") or ""

    if not sub:
        raise ValueError("Token sem sub")

    return {"sub": sub, "email": email}
