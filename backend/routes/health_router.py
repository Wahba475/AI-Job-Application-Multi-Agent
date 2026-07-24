"""Production health check — API / Redis / Database."""
from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from db.redis_client import ping_redis
from db.supabase_client import get_supabase, supabase_configured

logger = logging.getLogger("applyai.health")

router = APIRouter(tags=["health"])


async def _check_database() -> dict:
    if not supabase_configured():
        return {"status": "unconfigured", "ok": False}
    try:
        # Lightweight round-trip: select zero rows from users
        get_supabase().table("users").select("id").limit(1).execute()
        return {"status": "ok", "ok": True}
    except Exception as exc:
        logger.warning("Database health check failed: %s", exc)
        return {"status": "error", "ok": False, "detail": str(exc)}


@router.get("/health")
async def health():
    redis_ok = await ping_redis()
    db = await _check_database()

    redis = {"status": "ok" if redis_ok else "unavailable", "ok": redis_ok}
    api = {"status": "ok", "ok": True}

    if db["ok"] and redis_ok:
        overall = "healthy"
        code = 200
    elif db["ok"]:
        # Redis down → degraded (API + DB still serve; rate limits fail-open)
        overall = "degraded"
        code = 200
    else:
        overall = "unhealthy"
        code = 503

    body = {
        "status": overall,
        "api": api,
        "redis": redis,
        "database": db,
    }
    return JSONResponse(content=body, status_code=code)
