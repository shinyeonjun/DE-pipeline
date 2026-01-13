"""
Database Connection - Supabase Client
"""
from supabase import create_client, Client
from .config import settings

# Supabase client singleton
_supabase_client: Client | None = None


def get_supabase() -> Client:
    """Get Supabase client instance"""
    global _supabase_client
    
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
    
    return _supabase_client


# Export for convenience
supabase = get_supabase()

