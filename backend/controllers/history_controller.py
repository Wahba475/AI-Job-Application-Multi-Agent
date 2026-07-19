"""History CONTROLLER — thin HTTP handlers for the /history endpoints.

Responsibilities:
  - Parse the request (path params, auth user).
  - Call the history service.
  - Shape the HTTP response.
  - Map HistoryError → HTTPException.

No business logic lives here.
"""
from fastapi import Depends, HTTPException

from middleware.auth_middleware import get_current_user
from services.history_service import (
    HistoryError,
    delete_history_entry,
    get_download_url,
    get_history_entry,
    list_history,
)


def _handle(fn):
    """Thin wrapper: convert HistoryError → HTTPException."""
    async def _inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except HistoryError as e:
            raise HTTPException(status_code=e.status, detail=e.message)
    return _inner


# ── GET /history ───────────────────────────────────────────────────────────────

async def list_history_handler(user: dict = Depends(get_current_user)):
    """Return all history records for the authenticated user, newest first."""
    try:
        return list_history(user["id"])
    except HistoryError as e:
        raise HTTPException(status_code=e.status, detail=e.message)


# ── GET /history/{history_id} ──────────────────────────────────────────────────

async def get_history_handler(
    history_id: str,
    user: dict = Depends(get_current_user),
):
    """Return one history entry (ownership verified)."""
    try:
        return get_history_entry(history_id, user["id"])
    except HistoryError as e:
        raise HTTPException(status_code=e.status, detail=e.message)


# ── GET /history/{history_id}/download ────────────────────────────────────────

async def download_history_handler(
    history_id: str,
    user: dict = Depends(get_current_user),
):
    """Generate and return a fresh signed URL for the spreadsheet.
    The URL is never stored — it expires in 5 minutes."""
    try:
        url = get_download_url(history_id, user["id"])
        return {"download_url": url}
    except HistoryError as e:
        raise HTTPException(status_code=e.status, detail=e.message)


# ── DELETE /history/{history_id} ──────────────────────────────────────────────

async def delete_history_handler(
    history_id: str,
    user: dict = Depends(get_current_user),
):
    """Delete the spreadsheet from storage and remove the history record."""
    try:
        delete_history_entry(history_id, user["id"])
        return {"message": "History entry deleted"}
    except HistoryError as e:
        raise HTTPException(status_code=e.status, detail=e.message)
