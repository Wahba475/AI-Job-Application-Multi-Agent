"""Centralized runtime configuration.

All rate limits and Redis settings live here so new endpoints only need
to import a named dependency — never scatter magic numbers in routers.
"""
import os

# ── Redis ───────────────────────────────────────────────────────────────────
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_KEY_PREFIX: str = os.getenv("REDIS_KEY_PREFIX", "applyai:rl")

# ── Rate limits: (max_requests, window_seconds) ─────────────────────────────
# Change values here only — dependencies read from these constants.
PIPELINE_LIMIT_TIMES: int = int(os.getenv("PIPELINE_LIMIT_TIMES", "5"))
PIPELINE_LIMIT_SECONDS: int = int(os.getenv("PIPELINE_LIMIT_SECONDS", "3600"))  # 5/hour

AUTH_LIMIT_TIMES: int = int(os.getenv("AUTH_LIMIT_TIMES", "10"))
AUTH_LIMIT_SECONDS: int = int(os.getenv("AUTH_LIMIT_SECONDS", "60"))  # 10/minute

HISTORY_LIMIT_TIMES: int = int(os.getenv("HISTORY_LIMIT_TIMES", "60"))
HISTORY_LIMIT_SECONDS: int = int(os.getenv("HISTORY_LIMIT_SECONDS", "60"))  # 60/minute

# CORS (comma-separated origins, or defaults for local Vite)
_cors = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
)
CORS_ORIGINS: list[str] = [o.strip() for o in _cors.split(",") if o.strip()]
