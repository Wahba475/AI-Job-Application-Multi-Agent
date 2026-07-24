"""History ROUTER — maps URL paths to controller handlers.

All routes require authentication + history rate limit.
Effective paths (registered under /api in main.py):
  GET    /api/history
  GET    /api/history/{history_id}
  GET    /api/history/{history_id}/download
  DELETE /api/history/{history_id}
"""
from fastapi import APIRouter, Depends

from controllers.history_controller import (
    delete_history_handler,
    download_history_handler,
    get_history_handler,
    list_history_handler,
)
from middleware.auth_middleware import get_current_user
from middleware.rate_limiter_middleware import HistoryLimit

router = APIRouter(
    prefix="/history",
    tags=["history"],
    dependencies=[Depends(get_current_user), Depends(HistoryLimit)],
)

router.get("/")(list_history_handler)
router.get("/{history_id}")(get_history_handler)
router.get("/{history_id}/download")(download_history_handler)
router.delete("/{history_id}")(delete_history_handler)
