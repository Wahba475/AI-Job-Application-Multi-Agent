"""History ROUTER — maps URL paths to controller handlers.

Registered in main.py under the /api prefix, so effective paths are:
  GET    /api/history
  GET    /api/history/{history_id}
  GET    /api/history/{history_id}/download
  DELETE /api/history/{history_id}
"""
from backend.middleware.auth_middleware import get_current_user
from fastapi import Depends
from fastapi import APIRouter

from controllers.history_controller import (
    delete_history_handler,
    download_history_handler,
    get_history_handler,
    list_history_handler,
)

router = APIRouter(prefix="/history", tags=["history"],dependencies=[Depends(get_current_user)])

router.get("/")(list_history_handler)
router.get("/{history_id}")(get_history_handler)
router.get("/{history_id}/download")(download_history_handler)
router.delete("/{history_id}")(delete_history_handler)
