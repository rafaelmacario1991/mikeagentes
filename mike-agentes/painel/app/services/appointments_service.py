from datetime import datetime, timezone, timedelta
from app.services.supabase_client import get_admin_client

_BRASILIA = timezone(timedelta(hours=-3))


def localize_appointments(appointments: list[dict]) -> list[dict]:
    """Adiciona display_time e display_date (UTC-3 Brasília) em cada agendamento."""
    for apt in appointments:
        sa = apt.get("scheduled_at", "")
        if sa:
            try:
                dt = datetime.fromisoformat(sa.replace("Z", "+00:00"))
                dt_local = dt.astimezone(_BRASILIA)
                apt["display_time"] = dt_local.strftime("%H:%M")
                apt["display_date"] = dt_local.strftime("%Y-%m-%d")
            except Exception:
                apt["display_time"] = sa[11:16] if len(sa) >= 16 else "—"
                apt["display_date"] = sa[:10] if len(sa) >= 10 else ""
        else:
            apt["display_time"] = "—"
            apt["display_date"] = ""
    return appointments


# ── Clients ──────────────────────────────────────────────────────────────────

def search_clients(tenant_id: str, q: str) -> list[dict]:
    """Busca clientes por telefone ou nome (parcial, mínimo 2 chars)."""
    client = get_admin_client()
    q = q.strip()
    if len(q) < 2:
        return []
    # Escapa % e _ para evitar wildcard injection no ILIKE
    q_safe = q.replace("%", r"\%").replace("_", r"\_")
    result = (
        client.table("clients")
        .select("id, name, phone")
        .eq("tenant_id", tenant_id)
        .or_(f"phone.ilike.%{q_safe}%,name.ilike.%{q_safe}%")
        .limit(10)
        .execute()
    )
    return result.data or []


def get_or_create_client(tenant_id: str, name: str, phone: str) -> str:
    """Retorna o client_id. Cria o cliente se não existir pelo telefone."""
    client = get_admin_client()
    phone_clean = phone.strip().replace(" ", "")
    result = (
        client.table("clients")
        .select("id")
        .eq("tenant_id", tenant_id)
        .eq("phone", phone_clean)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]["id"]
    ins = client.table("clients").insert({
        "tenant_id": tenant_id,
        "name": name.strip(),
        "phone": phone_clean,
    }).execute()
    return ins.data[0]["id"]


# ── Slots ─────────────────────────────────────────────────────────────────────

def get_available_slots(tenant_id: str, professional_id: str, date_str: str) -> list[str]:
    """Retorna horários livres para um profissional numa data, respeitando intervalo."""
    from datetime import date as dt_date
    client = get_admin_client()

    d = dt_date.fromisoformat(date_str)
    # Python: Mon=0..Sun=6 → DB: Dom=0..Sab=6
    wd_db = (d.weekday() + 1) % 7

    avail_res = (
        client.table("availability")
        .select("start_time, end_time, break_start, break_end")
        .eq("tenant_id", tenant_id)
        .eq("professional_id", professional_id)
        .eq("weekday", wd_db)
        .eq("ativo", True)
        .limit(1)
        .execute()
    )
    if not avail_res.data:
        return []

    av = avail_res.data[0]

    appts_res = (
        client.table("appointments")
        .select("scheduled_at")
        .eq("tenant_id", tenant_id)
        .eq("professional_id", professional_id)
        .gte("scheduled_at", f"{date_str}T00:00:00+00:00")
        .lte("scheduled_at", f"{date_str}T23:59:59+00:00")
        .neq("status", "cancelled")
        .execute()
    )
    occupied = {a["scheduled_at"][11:16] for a in (appts_res.data or [])}

    def to_min(t):
        if not t:
            return None
        parts = str(t).split(":")
        return int(parts[0]) * 60 + int(parts[1])

    start = to_min(av["start_time"])
    end = to_min(av["end_time"])
    bs = to_min(av.get("break_start"))
    be = to_min(av.get("break_end"))

    slots = []
    c = start
    while c + 30 <= end:
        hh = str(c // 60).zfill(2)
        mm = str(c % 60).zfill(2)
        slot = f"{hh}:{mm}"
        in_break = (bs is not None and be is not None) and (c < be and c + 30 > bs)
        if not in_break and slot not in occupied:
            slots.append(slot)
        c += 30

    return slots


# ── Create ────────────────────────────────────────────────────────────────────

def create_appointment_manual(
    tenant_id: str,
    client_id: str,
    professional_id: str,
    service_id: str,
    date_str: str,
    time_str: str,
    duration_min: int,
    notes: str | None = None,
) -> dict:
    """Cria um agendamento manual com status 'scheduled'."""
    client = get_admin_client()
    scheduled_at = f"{date_str}T{time_str}:00-03:00"
    result = client.table("appointments").insert({
        "tenant_id": tenant_id,
        "client_id": client_id,
        "professional_id": professional_id,
        "service_id": service_id,
        "scheduled_at": scheduled_at,
        "duration_min": duration_min,
        "status": "scheduled",
        "notes": notes or None,
    }).execute()
    return result.data[0]


# ── List / Update ─────────────────────────────────────────────────────────────

def list_appointments(
    tenant_id: str,
    date_from: str | None = None,
    date_to: str | None = None,
    status: str | None = None,
) -> list[dict]:
    client = get_admin_client()
    query = (
        client.table("appointments")
        .select("*, professionals(name), services(name, duration_min), clients(name, phone)")
        .eq("tenant_id", tenant_id)
        .order("scheduled_at")
    )
    if date_from:
        query = query.gte("scheduled_at", f"{date_from}T00:00:00+00:00")
    if date_to:
        query = query.lte("scheduled_at", f"{date_to}T23:59:59+00:00")
    if status:
        query = query.eq("status", status)
    result = query.limit(500).execute()
    return localize_appointments(result.data or [])


def update_appointment_status(appointment_id: str, tenant_id: str, status: str) -> None:
    client = get_admin_client()
    client.table("appointments").update({"status": status}).eq("id", appointment_id).eq("tenant_id", tenant_id).execute()
