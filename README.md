# ApplyAI — AI Job-Application Multi-Agent

ApplyAI is a full-stack application that automates the most tedious part of a job
search: finding relevant openings and tailoring your CV to each one. You upload
your CV once and set a target role; a multi-agent AI pipeline searches live job
boards, filters to genuine matches, rewrites your CV per job to maximise its ATS
(Applicant Tracking System) score, validates every result for honesty, and hands
back ready-to-send `.docx` files plus a tracking spreadsheet.

Its defining principle is **honesty over vanity metrics**: the agent will never
invent skills or experience to inflate a match score. If you're a weak fit for a
role, it tells you your real ATS score and exactly which keywords you're missing
— useful career feedback instead of a fabricated CV that gets you rejected at
interview.

---

## Table of contents

- [What it does](#what-it-does)
- [The AI pipeline](#the-ai-pipeline)
- [The honest-CV philosophy](#the-honest-cv-philosophy)
- [Tech stack](#tech-stack)
- [Architecture](#architecture)
- [Directory structure](#directory-structure)
- [Getting started](#getting-started)
- [Environment variables](#environment-variables)
- [Database & storage setup](#database--storage-setup)
- [Running the app](#running-the-app)
- [API reference](#api-reference)
- [LLM providers](#llm-providers)
- [Security](#security)

---

## What it does

1. **Search** — queries live job listings (JSearch / RapidAPI) for your role,
   location, and experience level.
2. **Filter** — one AI call reads your actual CV and picks only the jobs you can
   honestly score well on (no point tailoring a Rust job for a Python CV).
3. **Tailor** — a ReAct agent rewrites your CV for each selected job, using only
   real content from your original CV, to maximise keyword/ATS match.
4. **Validate** — every tailored CV is scored against the job and checked for
   fabrication. You get an honest ATS score and a "missing from your CV" list.
5. **Deliver** — generates a formatted `.docx` per job and an `.xlsx` tracker,
   stores them, and shows a results page with previews, downloads, and per-job
   scores. Runs are saved to your history.

---

## The AI pipeline

The pipeline is a [LangGraph](https://langchain-ai.github.io/langgraph/)
`StateGraph` — a directed graph of nodes that pass a shared state object along.

```
START → search_jobs → filter_relevance → tailor_cv → validate_ats → build_deliverable → END
```

| Node | File | Responsibility |
|------|------|----------------|
| `search_jobs` | `ai/nodes/job_node.py` | Fetch listings from JSearch |
| `filter_relevance` | `ai/nodes/filter_node.py` | One batched CV-aware call selects the best matches |
| `tailor_cv` | `ai/nodes/tailor_cv_node.py` | ReAct agent rewrites the CV per job (runs jobs concurrently) |
| `validate_ats` | `ai/nodes/validate_ats_node.py` | Scores each CV + fabrication check + gap list |
| `build_deliverable` | `ai/nodes/build_deliverable_node.py` | Renders `.docx` CVs + `.xlsx` spreadsheet |

The **tailor** node is an agent, not a single prompt: it uses four tools
(`ai/tools/tailor_tools.py`) — `extract_jd_keywords`, `rewrite_cv_section`,
`check_ats_score`, `finalize_cv` — and decides how to apply them. The clean CV is
read from the `finalize_cv` tool's output, never from the model's chat message.

---

## The honest-CV philosophy

- **No fabrication.** The tailor prompt forbids inventing skills, metrics,
  employers, dates, or achievements. The validator independently flags any
  content not derivable from the original CV and rejects it.
- **Honest scores, no forcing.** There is no retry-loop that re-tailors a CV over
  and over to cross an arbitrary threshold. Each CV is scored once and delivered
  with its real number.
- **Actionable gaps.** Sub-70% results show a capped list of the exact keywords
  you're missing, and the UI labels them a "Stretch role" — so a junior applying
  to a senior post sees *why* it's a stretch instead of a fake-perfect CV.

---

## Tech stack

**Backend** — Python, FastAPI, LangGraph, LangChain. Auth via custom JWT
(`python-jose`) + bcrypt. Rate limiting via Redis (`fastapi-limiter`). Supabase
for Postgres + file storage.

**Frontend** — React 18 + Vite, React Router, Tailwind CSS, Axios, AOS
animations.

**AI / data** — LLM providers are pluggable (NVIDIA NIM / Groq / local Ollama);
job data from JSearch (RapidAPI); `.docx` via `python-docx`, `.xlsx` via
`openpyxl`.

---

## Architecture

The backend follows a layered, MERN-style separation so each file has one job:

```
route  →  controller  →  service  →  repository / external client
                              │
                          middleware (JWT verify, rate limit)
```

- **routes/** — map URL paths to handlers, attach auth + rate-limit dependencies.
- **controllers/** — thin: parse/validate the request, call a service, shape the
  response. No business logic.
- **services/** — business logic (auth, pipeline orchestration, storage, history).
- **repositories/** — direct database access (history rows).
- **middleware/** — `auth_middleware` (JWT verify, the `verifyToken` equivalent)
  and `rate_limiter_middleware` (per-route Redis limits).
- **db/** — Supabase and Redis clients, plus `schema.sql`.
- **config/** — all tunable constants (rate limits, CORS, Redis) in one place.

The AI pipeline lives in its own top-level `ai/` package so it's independent of
the web layer and could be reused or tested on its own.

---

## Directory structure

```
Job Agent/
├── ai/                              # LangGraph multi-agent pipeline (web-independent)
│   ├── graph.py                     # StateGraph wiring
│   ├── state.py                     # Shared pipeline state (TypedDict)
│   ├── nodes/                       # search / filter / tailor / validate / build
│   ├── tools/                       # LLM client, job search, CV/xlsx generators, tailor tools
│   └── skills/SKILL.md              # ATS scoring reference
├── backend/                         # FastAPI app
│   ├── main.py                      # App entry, CORS, router registration
│   ├── config/settings.py           # Rate limits, Redis, CORS constants
│   ├── routes/                      # auth / pipeline / history / health routers
│   ├── controllers/                 # Request handlers
│   ├── services/                    # auth, pipeline, storage, history, job_store
│   ├── repositories/                # history_repository (DB access)
│   ├── middleware/                  # auth (JWT) + rate limiter
│   ├── db/                          # supabase_client, redis_client, schema.sql
│   └── utils/cv_extractor.py        # PDF/DOCX → text
├── frontend/                        # React + Vite SPA
│   └── src/
│       ├── pages/                   # Landing, App, History, Login, Register
│       ├── components/              # JobCard, CVPreviewModal, FileUpload, Navbar, ...
│       ├── context/                 # AuthContext, PipelineContext
│       └── App.jsx / main.jsx
├── outputs/                         # Generated CVs + spreadsheet (gitignored)
├── requirements is at backend/requirements.txt
└── README.md
```

---

## Getting started

### Prerequisites

- **Python 3.11+** and **Node.js 18+**
- A **Supabase** project (free tier) — for auth, history, and file storage
- **Redis** (local or hosted) — for rate limiting
- API keys: **JSearch** (RapidAPI) for jobs, and at least one LLM provider
  (NVIDIA NIM is free and the default; Groq or local Ollama also supported)

### Install

```bash
# Backend
python -m venv venv
venv/Scripts/activate            # Windows;  source venv/bin/activate on macOS/Linux
pip install -r backend/requirements.txt

# Frontend
cd frontend
npm install
```

---

## Environment variables

Create a `.env` in the project root (never commit it — it's gitignored):

```env
# LLM provider: nvidia (free, default) | groq | ollama (local)
LLM_PROVIDER=nvidia
NVIDIA_API=nvapi-...
GROQ_API=gsk_...                 # only if LLM_PROVIDER=groq

# Job search
JSearch_API=...                  # RapidAPI JSearch key

# Supabase (auth + history + storage)
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_SERVICE_KEY=sb_secret_...   # service_role/secret key — backend only
SUPABASE_BUCKET=deliverables

# Auth
JWT_SECRET=<random 48+ char string>

# Redis (rate limiting)
REDIS_URL=redis://localhost:6379
```

Frontend `frontend/.env` (see `frontend/.env.example`):

```env
VITE_API_URL=http://127.0.0.1:8001
```

---

## Database & storage setup

1. In the Supabase dashboard, open **SQL Editor** and run
   [`backend/db/schema.sql`](backend/db/schema.sql). It creates:
   - `users` — email, bcrypt password hash (custom JWT auth, not Supabase Auth)
   - `runs` — one row per pipeline run, with a `jobs` JSONB column holding each
     job's ATS score, gaps, and stored-CV reference
2. Under **Storage**, create a **private** bucket named `deliverables`.
   Generated CVs and spreadsheets are uploaded to
   `deliverables/{user_id}/{run_id}/…` and served via short-lived **signed URLs**
   (never public).

---

## Running the app

```bash
# Terminal 1 — backend (from project root, so `backend.main` is importable)
uvicorn backend.main:app --reload --port 8001

# Terminal 2 — frontend
cd frontend
npm run dev            # http://localhost:5173
```

Flow: fill the form and upload a CV → if not logged in, a login/register modal
appears → after auth the pipeline runs → results page shows matched jobs with ATS
scores, gap lists, CV previews, and downloads. Every run is saved to **History**.

---

## API reference

All endpoints are prefixed with `/api`. Protected routes require
`Authorization: Bearer <jwt>`.

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| `POST` | `/auth/register` | — | Create account, returns `{ token, user }` |
| `POST` | `/auth/login` | — | Log in, returns `{ token, user }` |
| `GET` | `/auth/me` | ✅ | Current user from token |
| `POST` | `/run-pipeline` | ✅ | Start a run (multipart: form fields + CV file), returns `{ job_id }` |
| `GET` | `/status/{job_id}` | — | Poll run status/result |
| `GET` | `/history` | ✅ | List the user's past runs |
| `GET` | `/history/{id}` | ✅ | One run's full detail |
| `GET` | `/history/{id}/download` | ✅ | Signed URL for that run's spreadsheet |
| `DELETE` | `/history/{id}` | ✅ | Delete a run |
| `GET` | `/health` | — | Health check |

Runs are asynchronous: `POST /run-pipeline` returns a `job_id` immediately and the
frontend polls `GET /status/{job_id}` until `status` is `done` or `error`. This
means a page refresh mid-run resumes cleanly instead of restarting the pipeline.

---

## LLM providers

Set `LLM_PROVIDER` in `.env`. Configured in `ai/tools/llm_client.py`:

| Provider | Model | Cost | Notes |
|----------|-------|------|-------|
| `nvidia` (default) | `meta/llama-3.3-70b-instruct` | Free, no card | Instruct model → reliable tool-calling, no reasoning leak. Occasional endpoint congestion is absorbed by retries + an original-CV fallback |
| `groq` | `openai/gpt-oss-120b` | Free tier (8k TPM) / paid Dev tier | Fastest inference; the free tier throttles, the paid Dev tier (with a spend cap) is the path to sub-minute runs |
| `ollama` | `qwen2.5:7b` | Free, local | Unlimited and private, but slow on modest CPUs — best for offline correctness testing |

---

## Security

- **Passwords** are bcrypt-hashed; plaintext is never stored.
- **JWT** auth with a signed, expiring token; protected routes verified by
  `auth_middleware`.
- **Rate limiting** (Redis) per route — pipeline runs, auth attempts, and history
  reads each have their own limits, tunable in `config/settings.py`.
- **File uploads** are validated by extension (`.pdf`/`.docx` only) and capped at
  5 MB; temp files are deleted immediately after text extraction.
- **Downloads** use path-sanitised local serving and short-lived Supabase signed
  URLs — private storage, no public file access.
- **Secrets** (`.env`, `.mcp.json`, service keys) are gitignored and never shipped
  to the frontend, which only ever sees the public API origin.
```
