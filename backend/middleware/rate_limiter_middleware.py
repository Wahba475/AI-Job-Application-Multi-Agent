"""Reusable rate-limit dependencies (Redis + pyrate-limiter).

fastapi-limiter 0.2 RateLimiter walks app.routes and crashes on
`_IncludedRouter` (no `.path`) when routers are mounted via include_router —
causing silent fail-open. We call Limiter.try_acquire_async directly instead.

Usage:
    dependencies=[Depends(PipelineLimit)]
"""
from __future__ import annotations

import logging
from time import time_ns
from typing import Callable, Optional

from fastapi import HTTPException, Request, Response
from pyrate_limiter import (
    BucketFactory,
    Duration,
    Limiter,
    Rate,
    RateItem,
    RedisBucket,
)
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from config.settings import (
    AUTH_LIMIT_SECONDS,
    AUTH_LIMIT_TIMES,
    HISTORY_LIMIT_SECONDS,
    HISTORY_LIMIT_TIMES,
    PIPELINE_LIMIT_SECONDS,
    PIPELINE_LIMIT_TIMES,
    REDIS_KEY_PREFIX,
)
from db.redis_client import get_redis, is_redis_available
from services.auth_service import decode_token

logger = logging.getLogger("applyai.ratelimit")

_pipeline_limiter: Optional[Limiter] = None
_history_limiter: Optional[Limiter] = None
_auth_limiter: Optional[Limiter] = None


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "127.0.0.1"


async def ip_identifier(request: Request) -> str:
    return f"ip:{_client_ip(request)}"


async def jwt_or_ip_identifier(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()
        if token:
            payload = decode_token(token)
            if payload and payload.get("sub"):
                return f"user:{payload['sub']}"
    return f"ip:{_client_ip(request)}"


def _raise_429(request: Request) -> None:
    logger.warning(
        "Rate limit exceeded path=%s ip=%s",
        request.scope.get("path"),
        _client_ip(request),
    )
    raise HTTPException(
        status_code=HTTP_429_TOO_MANY_REQUESTS,
        detail="Too many requests. Please try again later.",
        headers={"Retry-After": "60"},
    )


class AsyncRedisBucketFactory(BucketFactory):
    def __init__(self, redis_client, rates: list[Rate], prefix: str):
        self.redis = redis_client
        self.rates = rates
        self.prefix = prefix
        self._cache: dict[str, RedisBucket] = {}

    async def wrap_item(self, name: str, weight: int = 1) -> RateItem:
        return RateItem(name=name, timestamp=time_ns() // 1_000_000, weight=weight)

    async def get(self, item: RateItem) -> RedisBucket:
        key = item.name
        bucket = self._cache.get(key)
        if bucket is None:
            bucket = await RedisBucket.init(
                self.rates,
                self.redis,
                f"{self.prefix}:{key}",
            )
            self.schedule_leak(bucket)
            self._cache[key] = bucket
        return bucket


def _make_limiter(times: int, seconds: int, name: str) -> Optional[Limiter]:
    client = get_redis()
    if client is None:
        return None
    rate = Rate(times, Duration.SECOND * seconds)
    factory = AsyncRedisBucketFactory(
        client,
        [rate],
        prefix=f"{REDIS_KEY_PREFIX}:{name}",
    )
    return Limiter(factory)


async def _enforce(
    limiter: Optional[Limiter],
    identifier: Callable,
    request: Request,
    response: Response,
) -> None:
    if limiter is None or not is_redis_available():
        return
    try:
        ident = await identifier(request)
        # Isolate counters per route path
        key = f"{ident}:{request.scope.get('path', '')}"
        ok = await limiter.try_acquire_async(key, blocking=False)
        if not ok:
            _raise_429(request)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(
            "Rate limiter failure (fail-open) path=%s error=%s",
            request.scope.get("path"),
            exc,
        )


async def PipelineLimit(request: Request, response: Response):
    await _enforce(_pipeline_limiter, jwt_or_ip_identifier, request, response)


async def HistoryLimit(request: Request, response: Response):
    await _enforce(_history_limiter, jwt_or_ip_identifier, request, response)


async def AuthLimit(request: Request, response: Response):
    await _enforce(_auth_limiter, ip_identifier, request, response)


def init_rate_limiters() -> None:
    global _pipeline_limiter, _history_limiter, _auth_limiter

    if not is_redis_available():
        _pipeline_limiter = _history_limiter = _auth_limiter = None
        logger.warning("Rate limiters not initialized — Redis unavailable")
        return

    _pipeline_limiter = _make_limiter(PIPELINE_LIMIT_TIMES, PIPELINE_LIMIT_SECONDS, "pipeline")
    _history_limiter = _make_limiter(HISTORY_LIMIT_TIMES, HISTORY_LIMIT_SECONDS, "history")
    _auth_limiter = _make_limiter(AUTH_LIMIT_TIMES, AUTH_LIMIT_SECONDS, "auth")
    logger.info(
        "Rate limiters ready pipeline=%s/%ss auth=%s/%ss history=%s/%ss",
        PIPELINE_LIMIT_TIMES,
        PIPELINE_LIMIT_SECONDS,
        AUTH_LIMIT_TIMES,
        AUTH_LIMIT_SECONDS,
        HISTORY_LIMIT_TIMES,
        HISTORY_LIMIT_SECONDS,
    )


def clear_rate_limiters() -> None:
    global _pipeline_limiter, _history_limiter, _auth_limiter
    _pipeline_limiter = _history_limiter = _auth_limiter = None
