import os
from functools import lru_cache
from supabase import create_client, Client


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    """Singleton Supabase client, created with the service_role key so the
    backend can read/write any table and manage Storage. This key is a SECRET —
    it lives only in the server .env and must never reach the frontend."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key or key.startswith("PASTE_"):
        raise RuntimeError(
            "Supabase not configured — set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env"
        )
    return create_client(url, key)


def supabase_configured() -> bool:
    key = os.getenv("SUPABASE_SERVICE_KEY", "")
    return bool(os.getenv("SUPABASE_URL")) and bool(key) and not key.startswith("PASTE_")
