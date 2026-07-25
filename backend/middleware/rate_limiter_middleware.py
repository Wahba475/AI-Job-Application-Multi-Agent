"""Pipeline rate limiting via raw Redis INCR + EXPIRE.

We bypass fastapi-limiter/pyrate-limiter on purpose: fastapi-limiter 0.2 walks
app.routes and crashes on included routers (silent fail-open), and a bucket
factory is overkill for a single counter. A plain GET → INCR → EXPIRE is atomic,
tiny, and fails open when Redis is down.
"""
from __future__ import annotations

import logging
import time
from threading import Lock

from fastapi import HTTPException, Request, Response
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from config.settings import (
    AUTH_LIMIT_SECONDS, AUTH_LIMIT_TIMES,
    PIPELINE_LIMIT_SECONDS, PIPELINE_LIMIT_TIMES, REDIS_KEY_PREFIX,
)
from db.redis_client import get_redis, is_redis_available
from services.auth_service import decode_token

logger = logging.getLogger("applyai.ratelimit")

# ── In-memory fallback (used when Redis is unavailable) ─────────────────────
# Redis is preferred so limits hold across multiple backend instances. But if
# Redis is down we must NOT fail fully open (that disables brute-force / abuse
# protection). This per-process fixed-window counter still enforces the limit
# for a single instance — the common case for this app.
_MEM: dict[str, tuple[int, float]] = {}   # key -> (count, window_start_epoch)
_MEM_LOCK = Lock()


def _enforce_memory(key: str, limit: int, window: int) -> None:
    now = time.time()
    with _MEM_LOCK:
        # Opportunistic prune so the dict can't grow unbounded.
        if len(_MEM) > 10_000:
            for k, (_, start) in list(_MEM.items()):
                if now - start >= window:
                    _MEM.pop(k, None)

        count, start = _MEM.get(key, (0, now))
        if now - start >= window:          # window elapsed → reset
            count, start = 0, now
        if count >= limit:
            raise HTTPException(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(int(window - (now - start)))},
            )
        _MEM[key] = (count + 1, start)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _identity(request: Request) -> str:
    """JWT subject if present (pipeline), else client IP."""
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()
        payload = decode_token(token) if token else None
        if payload and payload.get("sub"):
            return f"user:{payload['sub']}"
    return f"ip:{_client_ip(request)}"


async def _enforce(bucket: str, identity: str, limit: int, window: int):
    """Atomic Redis GET → INCR → EXPIRE fixed-window limiter. Fails open."""
    key = f"{REDIS_KEY_PREFIX}:{bucket}:{identity}"
    client = get_redis()
    if client is None or not is_redis_available():
        _enforce_memory(key, limit, window)   # Redis down → per-process fallback
        return
    try:
        current = await client.get(key)
        if current is not None and int(current) >= limit:
            raise HTTPException(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(window)},
            )
        pipe = client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        await pipe.execute()
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Rate limiter failure (fail-open): %s", exc)


async def PipelineLimit(request: Request, response: Response):
    await _enforce("pipeline", _identity(request),
                   PIPELINE_LIMIT_TIMES, PIPELINE_LIMIT_SECONDS)


async def AuthLimit(request: Request, response: Response):
    # Per-IP — brute-force / credential-stuffing protection for login/register.
    await _enforce("auth", f"ip:{_client_ip(request)}",
                   AUTH_LIMIT_TIMES, AUTH_LIMIT_SECONDS)


def init_rate_limiters() -> None:
    if is_redis_available():
        logger.info("Pipeline rate limit ready: %s per %ss", PIPELINE_LIMIT_TIMES, PIPELINE_LIMIT_SECONDS)
    else:
        logger.warning("Pipeline rate limit disabled — Redis unavailable (fail-open)")


def clear_rate_limiters() -> None:
    pass
