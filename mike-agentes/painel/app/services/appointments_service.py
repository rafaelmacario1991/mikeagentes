from app.services.supabase_client import get_admin_client


def list_appointments(tenant_id: str, date: str | None = None, status: str | None = None) -> list[dict]:
    client = get_admin_client()
    query = (
        client.table("appointments")
        .select("*, professionals(name), services(name, duration_min), clients(name, phone)")
        .eq("tenant_id", tenant_id)
        .order("scheduled_at")
    )
    if date:
        query = query.gte("scheduled_at", f"{date}T00:00:00").lte("scheduled_at", f"{date}T23:59:59")
    if status:
        query = query.eq("status", status)
    result = query.execute()
    return result.data or []


def update_appointment_status(appointment_id: str, tenant_id: str, status: str) -> None:
    client = get_admin_client()
    client.table("appointments").update({"status": status}).eq("id", appointment_id).eq("tenant_id", tenant_id).execute()
