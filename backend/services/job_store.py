"""Job store — status/result for async pipeline runs.

Backed by Redis (24h TTL) so results survive a server restart, with an
in-memory dict fallback when Redis is unavailable (dev / degraded mode).

A job record:
  { "status": "running|done|error", "step": <node name|null>,
    "result": <payload|null>, "error": <str|null> }
"""
import json
import uuid
import logging

from db.redis_client import get_redis_sync, redis_sync_available

logger = logging.getLogger("applyai.jobstore")

_TTL_SECONDS = 24 * 3600
_KEY = "applyai:job:"

# In-memory fallback (also used when Redis is down).
_mem: dict[str, dict] = {}


def _redis_set(job_id: str, record: dict) -> bool:
    if not redis_sync_available():
        return False
    try:
        get_redis_sync().set(_KEY + job_id, json.dumps(record), ex=_TTL_SECONDS)
        return True
    except Exception as e:
        logger.warning("job_store Redis set failed (%s) — using memory", e)
        return False


def _write(job_id: str, record: dict) -> None:
    if not _redis_set(job_id, record):
        _mem[job_id] = record


def create_job() -> str:
    job_id = uuid.uuid4().hex
    _write(job_id, {"status": "running", "step": None, "result": None, "error": None})
    return job_id


def set_step(job_id: str, step: str) -> None:
    job = get_job(job_id) or {"status": "running", "result": None, "error": None}
    job["step"] = step
    _write(job_id, job)


def set_result(job_id: str, result) -> None:
    _write(job_id, {"status": "done", "step": "done", "result": result, "error": None})


def set_error(job_id: str, error: str) -> None:
    _write(job_id, {"status": "error", "step": None, "result": None, "error": error})


def get_job(job_id: str):
    if redis_sync_available():
        try:
            raw = get_redis_sync().get(_KEY + job_id)
            if raw is not None:
                return json.loads(raw)
        except Exception as e:
            logger.warning("job_store Redis get failed (%s) — using memory", e)
    return _mem.get(job_id)
