from datetime import date, timedelta
from collections import defaultdict
from app.services.supabase_client import get_admin_client
from app.services.agent_service import get_agent_config
from app.services.appointments_service import localize_appointments


def resolve_period(period: str, start: str | None, end: str | None) -> tuple[date, date]:
    """Retorna (date_from, date_to) conforme o filtro selecionado."""
    today = date.today()
    if period == "tomorrow":
        d = today + timedelta(days=1)
        return d, d
    elif period == "week":
        monday = today - timedelta(days=today.weekday())
        return monday, monday + timedelta(days=6)
    elif period == "next_week":
        monday = today - timedelta(days=today.weekday()) + timedelta(weeks=1)
        return monday, monday + timedelta(days=6)
    elif period == "month":
        first = today.replace(day=1)
        # último dia do mês
        next_month = (first + timedelta(days=32)).replace(day=1)
        last = next_month - timedelta(days=1)
        return first, last
    elif period == "custom" and start and end:
        try:
            d_from = date.fromisoformat(start)
            d_to = date.fromisoformat(end)
            if d_to < d_from:
                d_from, d_to = d_to, d_from
            # Limita a 90 dias para evitar queries massivas
            if (d_to - d_from).days > 90:
                d_to = d_from + timedelta(days=90)
            return d_from, d_to
        except ValueError:
            pass
    # default: today
    return today, today


def get_dashboard_data(tenant_id: str, period: str = "today", start: str | None = None, end: str | None = None) -> dict:
    client = get_admin_client()
    date_from, date_to = resolve_period(period, start, end)

    result = (
        client.table("appointments")
        .select("*, professionals(name), services(name), clients(name, phone)")
        .eq("tenant_id", tenant_id)
        .gte("scheduled_at", f"{date_from.isoformat()}T00:00:00+00:00")
        .lte("scheduled_at", f"{date_to.isoformat()}T23:59:59+00:00")
        .order("scheduled_at")
        .limit(500)
        .execute()
    )
    appointments = localize_appointments(result.data or [])

    # Contadores
    total = len(appointments)
    confirmed  = sum(1 for a in appointments if a["status"] == "confirmed")
    pending    = sum(1 for a in appointments if a["status"] == "scheduled")
    cancelled  = sum(1 for a in appointments if a["status"] == "cancelled")
    completed  = sum(1 for a in appointments if a["status"] == "completed")

    # Agrupar por data (para exibição multi-dia)
    multi_day = date_from != date_to
    grouped: dict[str, list] = defaultdict(list)
    for apt in appointments:
        day = apt.get("display_date") or (apt["scheduled_at"][:10] if apt.get("scheduled_at") else "—")
        grouped[day].append(apt)
    appointments_grouped = [
        {"date": d, "rows": grouped[d]}
        for d in sorted(grouped.keys())
    ]

    # Status do agente
    agent = get_agent_config(tenant_id)

    # Labels de período para o template
    if date_from == date_to:
        period_label = date_from.strftime("%d/%m/%Y")
    else:
        period_label = f"{date_from.strftime('%d/%m/%Y')} — {date_to.strftime('%d/%m/%Y')}"

    return {
        "appointments_today": appointments,          # mantido por compatibilidade
        "appointments_grouped": appointments_grouped,
        "multi_day": multi_day,
        "total_today": total,
        "confirmed": confirmed,
        "pending": pending,
        "cancelled": cancelled,
        "completed": completed,
        "agent_active": agent.get("ativo", False) if agent else False,
        "agent_name": agent.get("agent_name", "Agente") if agent else "Agente",
        "today": date.today().isoformat(),
        "period": period,
        "period_label": period_label,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
    }
