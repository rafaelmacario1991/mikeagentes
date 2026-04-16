from supabase import create_client, Client
from app.config import settings

_admin_client: Client | None = None


def get_admin_client() -> Client:
    """Cliente com service_role — bypassa RLS, usado server-side."""
    global _admin_client
    if _admin_client is None:
        _admin_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    return _admin_client


def get_anon_client() -> Client:
    """Cliente com anon key — usado apenas para autenticação."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
