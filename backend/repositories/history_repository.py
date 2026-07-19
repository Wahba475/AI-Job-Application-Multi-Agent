"""History REPOSITORY — the only layer that talks to the ``history`` table.

Responsibilities:
  - Raw CRUD against the Supabase ``history`` table.
  - No business logic, no ownership checks, no HTTP knowledge.

Callers (history_service.py) are responsible for ownership validation before
they reach any mutating method here.
"""
from db.supabase_client import get_supabase


def create_entry(
    user_id: str,
    job_title: str,
    location: str | None,
    experience: str | None,
    spreadsheet_bucket: str,
    spreadsheet_path: str,
) -> dict:
    """Insert one history row and return the full inserted record."""
    result = (
        get_supabase()
        .table("history")
        .insert(
            {
                "user_id":            user_id,
                "job_title":          job_title,
                "location":           location,
                "experience":         experience,
                "spreadsheet_bucket": spreadsheet_bucket,
                "spreadsheet_path":   spreadsheet_path,
            }
        )
        .execute()
    )
    return result.data[0]


def list_by_user(user_id: str) -> list[dict]:
    """Return all history rows for *user_id*, newest first."""
    result = (
        get_supabase()
        .table("history")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


def get_by_id(history_id: str) -> dict | None:
    """Return one history row by primary key, or ``None`` if it does not exist."""
    result = (
        get_supabase()
        .table("history")
        .select("*")
        .eq("id", history_id)
        .execute()
    )
    return result.data[0] if result.data else None


def delete_by_id(history_id: str) -> None:
    """Delete one history row by primary key.  No-op if the row is already gone."""
    (
        get_supabase()
        .table("history")
        .delete()
        .eq("id", history_id)
        .execute()
    )
