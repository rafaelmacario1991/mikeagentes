from app.services.supabase_client import get_admin_client


def list_services(tenant_id: str, professional_id: str | None = None) -> list[dict]:
    client = get_admin_client()
    query = client.table("services").select("*, professionals(id, name)").eq("tenant_id", tenant_id)
    if professional_id:
        query = query.eq("professional_id", professional_id)
    result = query.order("name").execute()
    rows = result.data or []

    # Agrupa por nome para exibir serviços únicos com múltiplos profissionais
    grouped: dict[str, dict] = {}
    for svc in rows:
        key = svc["name"]
        if key not in grouped:
            grouped[key] = {
                **svc,
                "professionals_list": [],
                "all_ids": [],
            }
        if svc.get("professionals"):
            grouped[key]["professionals_list"].append(svc["professionals"]["name"])
            grouped[key]["all_ids"].append(svc["id"])
        # Mantém o ativo = True se qualquer versão estiver ativa
        if svc.get("ativo"):
            grouped[key]["ativo"] = True

    return list(grouped.values())


def get_service(service_id: str, tenant_id: str) -> dict | None:
    client = get_admin_client()
    result = (
        client.table("services")
        .select("*")
        .eq("id", service_id)
        .eq("tenant_id", tenant_id)
        .maybe_single()
        .execute()
    )
    return result.data


def create_service(tenant_id: str, professional_id: str, name: str, duration_minutes: int, price: float) -> dict:
    client = get_admin_client()
    result = client.table("services").insert({
        "tenant_id": tenant_id,
        "professional_id": professional_id,
        "name": name,
        "duration_min": duration_minutes,
        "price": price,
        "ativo": True,
    }).execute()
    return result.data[0]


def update_service(service_id: str, tenant_id: str, name: str, duration_minutes: int, price: float, professional_id: str) -> None:
    client = get_admin_client()
    client.table("services").update({
        "name": name,
        "duration_min": duration_minutes,
        "price": price,
        "professional_id": professional_id,
    }).eq("id", service_id).eq("tenant_id", tenant_id).execute()


def sync_service_professionals(
    service_id: str,
    tenant_id: str,
    name: str,
    duration_min: int,
    price: float,
    professional_ids: list[str],
) -> None:
    """Sincroniza um serviço (por nome) entre múltiplos profissionais.

    - Atualiza o registro base (service_id).
    - Cria novos registros para profissionais adicionados.
    - Desativa registros de profissionais removidos.
    """
    client = get_admin_client()

    # Descobre o nome antigo do serviço para encontrar todos os registros irmãos
    current = (
        client.table("services").select("name, professional_id")
        .eq("id", service_id).maybe_single().execute().data
    )
    if not current:
        return
    old_name = current["name"]

    # Busca todos os serviços com o mesmo nome neste tenant
    siblings = (
        client.table("services").select("id, professional_id")
        .eq("tenant_id", tenant_id).eq("name", old_name).execute().data or []
    )
    existing: dict[str, str] = {s["professional_id"]: s["id"] for s in siblings}

    # Atualiza todos os registros existentes com os novos dados
    for pro_id, svc_id in existing.items():
        if pro_id in professional_ids:
            client.table("services").update({
                "name": name, "duration_min": duration_min, "price": price, "ativo": True,
            }).eq("id", svc_id).execute()
        else:
            # Profissional desmarcado → desativa
            client.table("services").update({"ativo": False}).eq("id", svc_id).execute()

    # Cria registros para profissionais recém-selecionados
    for pro_id in professional_ids:
        if pro_id not in existing:
            client.table("services").insert({
                "tenant_id": tenant_id,
                "professional_id": pro_id,
                "name": name,
                "duration_min": duration_min,
                "price": price,
                "ativo": True,
            }).execute()


def toggle_service(service_id: str, tenant_id: str, is_active: bool) -> None:
    client = get_admin_client()
    client.table("services").update({"ativo": is_active}).eq("id", service_id).eq("tenant_id", tenant_id).execute()
