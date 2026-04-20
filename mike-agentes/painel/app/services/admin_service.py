import re
from app.services.supabase_client import get_admin_client


def list_tenants() -> list[dict]:
    client = get_admin_client()
    result = client.table("tenants").select("*").order("name").execute()
    return result.data or []


def toggle_tenant(tenant_id: str, is_active: bool) -> None:
    client = get_admin_client()
    client.table("tenants").update({"ativo": is_active}).eq("id", tenant_id).execute()


def get_tenant(tenant_id: str) -> dict | None:
    client = get_admin_client()
    result = client.table("tenants").select("*").eq("id", tenant_id).limit(1).execute()
    return result.data[0] if result.data else None


def create_tenant(name: str, email: str, password: str, plan: str = "starter") -> str | None:
    """
    Cria um tenant no DB e um usuário no Supabase Auth.
    Retorna None em caso de sucesso, ou uma string de erro.
    """
    if len(password) < 6:
        return "A senha deve ter pelo menos 6 caracteres."

    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

    client = get_admin_client()

    # Verificar se email já existe
    existing = client.table("tenants").select("id").eq("email", email).limit(1).execute()
    if existing.data:
        return "Já existe um tenant com este email."

    # Criar tenant no DB
    try:
        result = client.table("tenants").insert({
            "name": name,
            "slug": slug,
            "email": email,
            "plan": plan,
            "ativo": True,
        }).execute()
    except Exception as e:
        return f"Erro ao criar tenant: {str(e)}"

    # Criar usuário no Supabase Auth
    try:
        client.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,
        })
    except Exception as e:
        # Rollback: apagar tenant criado
        if result.data:
            tenant_id = result.data[0]["id"]
            client.table("tenants").delete().eq("id", tenant_id).execute()
        return f"Erro ao criar usuário: {str(e)}"

    return None
