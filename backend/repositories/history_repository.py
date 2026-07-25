"""History REPOSITORY — the only layer that talks to the ``history`` table.

Raw CRUD only. Ownership checks live in history_service.py.

Row shape (see backend/db/schema.sql):
  id, user_id, run_id, job_title, location, experience,
  spreadsheet_bucket, spreadsheet_path, jobs (JSONB), created_at
"""
from db.supabase_client import get_supabase


def create_entry(
    user_id: str,
    run_id: str,
    job_title: str,
    location: str | None,
    experience: str | None,
    spreadsheet_bucket: str,
    spreadsheet_path: str,
    jobs: list[dict],
) -> dict:
    """Insert one history row and return the full inserted record."""
    result = (
        get_supabase()
        .table("history")
        .insert({
            "user_id":            user_id,
            "run_id":             run_id,
            "job_title":          job_title,
            "location":           location,
            "experience":         experience,
            "spreadsheet_bucket": spreadsheet_bucket,
            "spreadsheet_path":   spreadsheet_path,
            "jobs":               jobs,
        })
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
    """Return one history row by primary key, or ``None``."""
    result = (
        get_supabase()
        .table("history")
        .select("*")
        .eq("id", history_id)
        .execute()
    )
    return result.data[0] if result.data else None


def delete_by_id(history_id: str) -> None:
    """Delete one history row by primary key. No-op if already gone."""
    get_supabase().table("history").delete().eq("id", history_id).execute()
