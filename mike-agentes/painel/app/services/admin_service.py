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
    result = client.table("tenants").select("*").eq("id", tenant_id).maybe_single().execute()
    return result.data
