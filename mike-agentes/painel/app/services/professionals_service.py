from app.services.supabase_client import get_admin_client


def list_professionals(tenant_id: str) -> list[dict]:
    client = get_admin_client()
    result = client.table("professionals").select("*").eq("tenant_id", tenant_id).order("name").execute()
    return result.data or []


def get_professional(professional_id: str, tenant_id: str) -> dict | None:
    client = get_admin_client()
    result = (
        client.table("professionals")
        .select("*")
        .eq("id", professional_id)
        .eq("tenant_id", tenant_id)
        .maybe_single()
        .execute()
    )
    return result.data


def create_professional(tenant_id: str, name: str, specialty: str) -> dict:
    client = get_admin_client()
    result = client.table("professionals").insert({
        "tenant_id": tenant_id,
        "name": name,
        "role": specialty,
        "ativo": True,
    }).execute()
    return result.data[0]


def update_professional(professional_id: str, tenant_id: str, name: str, specialty: str) -> None:
    client = get_admin_client()
    client.table("professionals").update({
        "name": name,
        "role": specialty,
    }).eq("id", professional_id).eq("tenant_id", tenant_id).execute()


def toggle_professional(professional_id: str, tenant_id: str, is_active: bool) -> None:
    client = get_admin_client()
    client.table("professionals").update({"ativo": is_active}).eq("id", professional_id).eq("tenant_id", tenant_id).execute()
