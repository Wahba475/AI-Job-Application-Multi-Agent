import sys
import os
import logging
from contextlib import asynccontextmanager

# Windows console defaults to cp1252, which crashes on non-ASCII prints
# (accented job titles, unicode arrows, emoji) coming from job descriptions
# and pipeline logging. Force UTF-8 so those never take the process down.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Add project root to sys.path so the 'ai' package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

# Load project-root .env regardless of process cwd (Railway / local / uvicorn --app-dir)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_ROOT, ".env"))
load_dotenv()  # also allow cwd overrides

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("applyai")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import CORS_ORIGINS
from db.redis_client import close_redis, init_redis
from middleware.rate_limiter_middleware import clear_rate_limiters, init_rate_limiters
from routes.auth_router import router as auth_router
from routes.health_router import router as health_router
from routes.history_router import router as history_router
from routes.pipeline_router import router as pipeline_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting ApplyAI API")
    await init_redis()
    init_rate_limiters()
    yield
    clear_rate_limiters()
    await close_redis()
    logger.info("ApplyAI API shut down")


app = FastAPI(title="ApplyAI — Job Application Agent API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)                # GET /health
app.include_router(auth_router, prefix="/api")   # /api/auth/*
app.include_router(pipeline_router, prefix="/api")
app.include_router(history_router, prefix="/api")
