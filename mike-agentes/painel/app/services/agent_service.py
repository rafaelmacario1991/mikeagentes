from app.services.supabase_client import get_admin_client


def get_agent_config(tenant_id: str) -> dict | None:
    client = get_admin_client()
    result = client.table("agent_configs").select("*").eq("tenant_id", tenant_id).limit(1).execute()
    return result.data[0] if result.data else None


def upsert_agent_config(tenant_id: str, data: dict) -> dict:
    client = get_admin_client()
    data["tenant_id"] = tenant_id
    result = client.table("agent_configs").upsert(data, on_conflict="tenant_id").execute()
    return result.data[0] if result.data else {}


def toggle_agent(tenant_id: str, is_active: bool) -> None:
    client = get_admin_client()
    client.table("agent_configs").update({"ativo": is_active}).eq("tenant_id", tenant_id).execute()
