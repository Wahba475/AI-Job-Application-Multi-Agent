"""Supabase Storage helpers.

Responsibilities (and ONLY these):
  1. Upload a file  → returns (bucket, path).  No signed URL is created here.
  2. Delete a file  → removes the object from the bucket.
  3. Generate a signed URL → called at download-time only; result is NEVER stored.

Design rule: this service knows nothing about the history table, user records, or
any other business logic.  It only speaks to Supabase Storage.
"""
import os
from db.supabase_client import get_supabase

BUCKET = os.getenv("SUPABASE_BUCKET", "deliverables")

# Content-type constants reused by callers.
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# Signed URLs are short-lived (5 min) — they are never persisted.
_SIGNED_URL_TTL_SECONDS = 5 * 60


def upload_file(
    user_id: str,
    run_id: str,
    filename: str,
    data: bytes,
    content_type: str,
) -> tuple[str, str]:
    """Upload *data* to ``{bucket}/{user_id}/{run_id}/{filename}``.

    Returns ``(bucket, path)`` — the caller is responsible for persisting
    these two values in the database.  No signed URL is created.
    """
    sb   = get_supabase()
    path = f"{user_id}/{run_id}/{filename}"

    sb.storage.from_(BUCKET).upload(
        path=path,
        file=data,
        file_options={"content-type": content_type, "upsert": "true"},
    )

    return BUCKET, path


def generate_signed_url(bucket: str, path: str, ttl_seconds: int = _SIGNED_URL_TTL_SECONDS) -> str:
    """Create a *temporary* signed download URL for an existing object.

    This is the ONLY place signed URLs are created.  They are returned to the
    caller and must never be stored in the database.
    """
    sb     = get_supabase()
    signed = sb.storage.from_(bucket).create_signed_url(path, ttl_seconds)
    # supabase-py v1 returns {"signedURL": "..."}, v2 returns {"signed_url": "..."}
    return signed.get("signedURL") or signed.get("signed_url", "")


def delete_file(bucket: str, path: str) -> None:
    """Remove a single object from storage.

    If the object does not exist the call is silently treated as a no-op so
    callers do not need to guard against double-deletes.
    """
    get_supabase().storage.from_(bucket).remove([path])
