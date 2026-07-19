"""History SERVICE — business logic for all history operations.

Responsibilities:
  - Ownership verification before any read or mutation.
  - Orchestrating repository (DB) and storage_service (files).
  - Raising HistoryError so controllers can map them to HTTP codes.

Controllers call this layer.  This layer never knows about HTTP.
"""
import repositories.history_repository as history_repo
import services.storage_service as storage_svc


class HistoryError(Exception):
    """Raised for history-specific failures; controllers map these to HTTP codes."""

    def __init__(self, status: int, message: str):
        self.status  = status
        self.message = message
        super().__init__(message)


# ── helpers ────────────────────────────────────────────────────────────────────

def _get_and_verify(history_id: str, user_id: str) -> dict:
    """Fetch a history entry and confirm the requesting user owns it.

    Raises HistoryError(404) if not found.
    Raises HistoryError(403) if the row belongs to a different user.
    """
    entry = history_repo.get_by_id(history_id)
    if entry is None:
        raise HistoryError(404, "History entry not found")
    if entry["user_id"] != user_id:
        raise HistoryError(403, "Access denied")
    return entry


# ── public API ─────────────────────────────────────────────────────────────────

def create_history_entry(
    user_id: str,
    job_title: str,
    location: str | None,
    experience: str | None,
    spreadsheet_bucket: str,
    spreadsheet_path: str,
) -> dict:
    """Persist one history record.  Called by the pipeline controller after a
    successful storage upload."""
    return history_repo.create_entry(
        user_id=user_id,
        job_title=job_title,
        location=location,
        experience=experience,
        spreadsheet_bucket=spreadsheet_bucket,
        spreadsheet_path=spreadsheet_path,
    )


def list_history(user_id: str) -> list[dict]:
    """Return all history entries for the authenticated user, newest first."""
    return history_repo.list_by_user(user_id)


def get_history_entry(history_id: str, user_id: str) -> dict:
    """Return one history entry after verifying ownership."""
    return _get_and_verify(history_id, user_id)


def get_download_url(history_id: str, user_id: str) -> str:
    """Verify ownership, then generate a *fresh* signed URL for the spreadsheet.

    The signed URL is returned to the caller and is NEVER stored.
    """
    entry = _get_and_verify(history_id, user_id)
    return storage_svc.generate_signed_url(
        bucket=entry["spreadsheet_bucket"],
        path=entry["spreadsheet_path"],
    )


def delete_history_entry(history_id: str, user_id: str) -> None:
    """Verify ownership, delete the file from storage, then delete the DB row.

    Order matters:
      1. Confirm ownership (raises before any mutation if check fails).
      2. Delete from storage (if this fails, the DB row is still intact —
         the user can retry the delete).
      3. Delete the DB row (only reached if storage delete succeeded).
    """
    entry = _get_and_verify(history_id, user_id)

    storage_svc.delete_file(
        bucket=entry["spreadsheet_bucket"],
        path=entry["spreadsheet_path"],
    )

    history_repo.delete_by_id(history_id)
