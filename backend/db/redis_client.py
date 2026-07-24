"""Redis client lifecycle — temporary runtime state only (rate-limit counters).

Graceful degradation: if Redis is unreachable the app still starts and serves
traffic; rate limiting fails open until Redis recovers.
"""
from __future__ import annotations

import logging
from typing import Optional

import redis.asyncio as redis

from config.settings import REDIS_URL

logger = logging.getLogger("applyai.redis")

_client: Optional[redis.Redis] = None
_available: bool = False


def is_redis_available() -> bool:
    return _available and _client is not None


def get_redis() -> Optional[redis.Redis]:
    """Return the shared async Redis client, or None if unavailable."""
    return _client if _available else None


async def init_redis() -> bool:
    """Connect during FastAPI startup. Never raises — fails open on error."""
    global _client, _available

    try:
        client = redis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        await client.ping()
        _client = client
        _available = True
        logger.info("Redis connected (%s)", REDIS_URL.split("@")[-1])
        return True
    except Exception as exc:
        _client = None
        _available = False
        logger.warning(
            "Redis unavailable — rate limiting disabled (fail-open). url=%s error=%s",
            REDIS_URL.split("@")[-1],
            exc,
        )
        return False


async def close_redis() -> None:
    """Close during FastAPI shutdown."""
    global _client, _available

    if _client is None:
        _available = False
        return

    try:
        await _client.aclose()
        logger.info("Redis connection closed")
    except Exception as exc:
        logger.warning("Redis shutdown error: %s", exc)
    finally:
        _client = None
        _available = False


async def ping_redis() -> bool:
    """Health-check ping. Updates availability flag on recovery / loss."""
    global _available

    client = _client
    if client is None:
        # Attempt reconnect if we never connected (or previously failed)
        return await init_redis()

    try:
        await client.ping()
        if not _available:
            _available = True
            logger.info("Redis reconnected")
        return True
    except Exception as exc:
        if _available:
            logger.warning("Redis lost — rate limiting failing open. error=%s", exc)
        _available = False
        return False
