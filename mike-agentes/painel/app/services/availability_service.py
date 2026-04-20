from app.services.supabase_client import get_admin_client


def get_week_availability(tenant_id: str, professional_id: str) -> dict[int, dict]:
    """Retorna dict indexado por weekday (0=Dom...6=Sab)."""
    client = get_admin_client()
    result = (
        client.table("availability")
        .select("*")
        .eq("tenant_id", tenant_id)
        .eq("professional_id", professional_id)
        .execute()
    )
    by_day = {}
    for row in (result.data or []):
        by_day[row["weekday"]] = row
    return by_day


def save_week_availability(tenant_id: str, professional_id: str, days: list[dict]) -> None:
    """
    Recebe lista de 7 dicts: [{index, active, start, end}, ...].
    Faz delete + insert para garantir consistência.
    """
    client = get_admin_client()
    client.table("availability").delete().eq("tenant_id", tenant_id).eq("professional_id", professional_id).execute()

    rows = []
    for day in days:
        if day.get("active"):
            break_start = day.get("break_start") or None
            break_end   = day.get("break_end")   or None
            # Ignora intervalo se só um dos campos foi preenchido
            if not break_start or not break_end:
                break_start = break_end = None
            rows.append({
                "tenant_id": tenant_id,
                "professional_id": professional_id,
                "weekday": day["index"],
                "start_time": day["start"],
                "end_time": day["end"],
                "break_start": break_start,
                "break_end": break_end,
                "ativo": True,
            })
    if rows:
        client.table("availability").insert(rows).execute()
