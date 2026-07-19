import sys
import os

# Windows console defaults to cp1252, which crashes on non-ASCII prints
# (accented job titles, unicode arrows, emoji) coming from job descriptions
# and pipeline logging. Force UTF-8 so those never take the process down.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Add project root to sys.path so the 'ai' package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.pipeline_router import router as pipeline_router
from routes.auth_router import router as auth_router
from routes.history_router import router as history_router

app = FastAPI(title="ApplyAI — Job Application Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")       # /api/auth/*
app.include_router(pipeline_router, prefix="/api")   # /api/run-pipeline, /api/status/*, ...
app.include_router(history_router, prefix="/api")    # /api/history/*
