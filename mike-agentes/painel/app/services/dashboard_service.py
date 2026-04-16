from datetime import date
from app.services.supabase_client import get_admin_client
from app.services.agent_service import get_agent_config


def get_dashboard_data(tenant_id: str) -> dict:
    client = get_admin_client()
    today = date.today().isoformat()

    # Agendamentos de hoje
    result = (
        client.table("appointments")
        .select("*, professionals(name), services(name), clients(name, phone)")
        .eq("tenant_id", tenant_id)
        .gte("scheduled_at", f"{today}T00:00:00")
        .lte("scheduled_at", f"{today}T23:59:59")
        .order("scheduled_at")
        .execute()
    )
    appointments_today = result.data or []

    # Contadores rápidos
    total_today = len(appointments_today)
    confirmed = sum(1 for a in appointments_today if a["status"] == "confirmed")
    pending = sum(1 for a in appointments_today if a["status"] == "scheduled")
    cancelled = sum(1 for a in appointments_today if a["status"] == "cancelled")

    # Status do agente
    agent = get_agent_config(tenant_id)

    return {
        "appointments_today": appointments_today,
        "total_today": total_today,
        "confirmed": confirmed,
        "pending": pending,
        "cancelled": cancelled,
        "agent_active": agent.get("ativo", False) if agent else False,
        "agent_name": agent.get("agent_name", "Agente") if agent else "Agente",
        "today": today,
    }
