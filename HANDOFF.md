# ApplyAI — Session Handoff

## Project

Job application AI agent. User fills form + uploads CV → pipeline searches jobs, filters, tailors CV per job using LLM agent, validates ATS score, generates .docx files + spreadsheet.

**Stack:** FastAPI backend, React+Vite frontend, LangGraph pipeline, Groq LLM, JSearch API (RapidAPI).

---

## Folder Structure (clean, no duplicates)

```
Job Agent/
├── ai/                         # LangGraph pipeline (Python package)
│   ├── __init__.py
│   ├── graph.py                # LangGraph StateGraph definition
│   ├── state.py                # JobAgentState TypedDict
│   ├── nodes/
│   │   ├── job_node.py         # search_jobs_node
│   │   ├── filter_node.py      # filter_relevance_node (caps at 5 jobs)
│   │   ├── tailor_cv_node.py   # ReAct agent with 4 tools (uses agent_llm)
│   │   ├── validate_ats_node.py
│   │   └── build_deliverable_node.py
│   ├── tools/
│   │   ├── llm_client.py       # llm + agent_llm instances
│   │   ├── search_job.py       # JSearch v2 API
│   │   ├── tailor_tools.py     # 4 LangChain @tools with retry backoff
│   │   ├── cv_generator.py
│   │   └── spreadsheet_builder.py
│   └── skills/
│       └── SKILL.md            # ATS scoring methodology (used by validate node only now)
├── backend/
│   ├── main.py                 # FastAPI app, CORS, sys.path setup
│   ├── routes/pipeline_router.py
│   ├── controllers/pipeline_controller.py
│   ├── services/pipeline_service.py   # calls pipeline.invoke()
│   └── utils/cv_extractor.py
├── frontend/                   # Vite + React 18
│   ├── src/
│   │   ├── App.jsx             # AOS init, Router, PipelineProvider
│   │   ├── pages/
│   │   │   ├── LandingPage.jsx
│   │   │   ├── AppPage.jsx     # 3 states: form / loading / results
│   │   │   └── HistoryPage.jsx
│   │   ├── components/
│   │   │   ├── JobCard.jsx
│   │   │   ├── CVPreviewModal.jsx
│   │   │   ├── LoadingSteps.jsx
│   │   │   └── FileUpload.jsx
│   │   ├── context/PipelineContext.jsx
│   │   └── services/api.js     # baseURL: http://localhost:8001/api
│   └── tailwind.config.js      # Stitch design tokens
├── outputs/                    # Generated CVs + spreadsheet go here
│   ├── CVs/
│   └── jobs.xlsx
├── .env                        # GROQ_API, JSearch_API, OpenRouter_API
├── .mcp.json                   # Stitch MCP + Playwright MCP configs
└── venv/
```

---

## How to Run

```powershell
# Terminal 1 — Backend
cd "c:\Users\L\OneDrive\Desktop\Job Agent"
venv/scripts/activate
uvicorn backend.main:app --reload --port 8001

# Terminal 2 — Frontend
cd frontend
npm run dev
# Opens at http://localhost:5173
```

---

## Current State of Key Files

### `ai/tools/llm_client.py`
```python
import os
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API"), temperature=0)
agent_llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API"), temperature=0)
# NOTE: agent_llm should be switched to Ollama or Gemini — see TODO below
```

### `ai/tools/search_job.py`
- Fixed endpoint: `https://jsearch.p.rapidapi.com/search-v2`
- Fixed data path: `data["data"]["jobs"]` (not `data["data"]`)
- No `fields` param, no `country=eg`, `date_posted=month`, `num_pages=2`

### `ai/tools/tailor_tools.py`
- 4 `@tool` functions: `extract_jd_keywords`, `rewrite_cv_section`, `check_ats_score`, `finalize_cv`
- All use `_invoke()` wrapper with 429 retry backoff (5s, 10s, 15s, 20s)

### `ai/nodes/tailor_cv_node.py`
- `create_react_agent(agent_llm, _tailor_tools)` — ReAct agent architecture KEPT
- System prompt is SHORT (no SKILL.md embedded) — was causing token overflow
- `time.sleep(3)` between jobs to avoid TPM rate limit
- SKILL.md is only used in `validate_ats_node.py`

### `ai/nodes/filter_node.py`
- Caps output at 5 jobs: `return {"filtered_jobs": relevant[:5]}`

---

## Problems Fixed This Session

| Problem | Root Cause | Fix |
|---------|-----------|-----|
| JSearch 404 | Endpoint renamed `/search` → `/search-v2` in API v5 | Updated URL |
| JSearch returns 0 jobs | `data["data"]` is a dict `{jobs:[], cursor:null}`, not a list | Use `data["data"]["jobs"]` |
| JSearch `country=eg` returns 0 | Egypt has almost no JSearch listings | Removed country param |
| Tailor agent `tool_use_failed` | `llama-3.3-70b-versatile` generates old `<function=...>` format when system prompt is very large (SKILL.md = 1741 words) | Removed SKILL.md from tailor prompt, kept it only in validate node |
| `llama3-groq-70b-8192-tool-use-preview` | Model decommissioned by Groq | Switched to versatile |
| OpenRouter 402 | Claude Haiku requires paid credits | Switched to free tier then hit rate limit |
| Groq TPM (12K/min) | Processing 15 jobs × 5 LLM calls each | Capped at 5 jobs, added 3s delay, retry backoff in tools |
| Groq TPD (100K/day) | ~100K tokens per test run × many test runs = daily limit hit | Need local model or Gemini |
| Root-level duplicate folders | Old `Nodes/`, `Tools/`, `Skills/`, `graph.py`, `state.py` at root | DELETED ✓ |

---

## TODO — Next Session

### Priority 1: Switch LLM to local Ollama
- Ollama installed (v0.24.0), `qwen2.5:0.5b` too small
- Pull: `ollama pull qwen2.5:7b` (4.7GB) or `llama3.1:8b` (4.9GB)
- Update `llm_client.py`:
```python
from langchain_ollama import ChatOllama
llm = ChatOllama(model="qwen2.5:7b", temperature=0)
agent_llm = ChatOllama(model="qwen2.5:7b", temperature=0)
```
- Install: `pip install langchain-ollama`
- Start Ollama before running: `ollama serve`

### Priority 2: Add Gemini Flash as production LLM
- Free tier: 1M tokens/day (vs Groq 100K)
- Key: Get from Google AI Studio (aistudio.google.com) — free
- Add to `.env`: `GEMINI_API=...`
- Install: `pip install langchain-google-genai`
- Usage:
```python
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=os.getenv("GEMINI_API"))
```

### Priority 3: Code cleanup in tailor_cv_node.py
- Remove `time.sleep(3)` (only needed due to Groq rate limits — local model doesn't need it)
- Keep the retry in `tailor_tools.py` (still useful for network errors)
- `agent_llm` and `llm` can be same model or different — decide based on final LLM choice

### Priority 4: Test full pipeline end-to-end from frontend
- Restart backend, open http://localhost:5173/app
- Fill form: job title, location, experience, upload a real CV PDF
- Should see loading → results with job cards, ATS scores, CV preview, download buttons
- Test CV download (.docx)
- Test spreadsheet download

### Priority 5: Playwright MCP testing
- Already configured in `.mcp.json`
- Restart VS Code to load it, then use it to test the full UI flow

---

## LLM Strategy Decision (discuss next session)

| Option | Cost | Tokens/day | Quality | Effort |
|--------|------|-----------|---------|--------|
| **Ollama local** (qwen2.5:7b) | Free | Unlimited | Good | Low |
| **Gemini Flash** (free tier) | Free | 1M/day | Excellent | Low |
| **Groq** (current) | Free | 100K/day | Excellent | Done |
| **OpenRouter** (free models) | Free | Rate limited | Variable | Low |
| **OpenAI gpt-4o-mini** | ~$0.015/run | Unlimited | Excellent | Low |

**Recommendation:** Use Ollama for local dev, Gemini Flash for demo/production.

---

## .env Keys Available
```
GROQ_API=gsk_XcQ6yoquIW...          # LLM — 100K tokens/day free
JSearch_API=fc4f0c4941mshf...        # Job search — subscribed, working
OpenRouter_API=sk-or-v1-3672e2ea...  # Backup LLM — free tier rate limited
```

---

## Architecture Notes

- **ReAct agent in tailor_cv_node MUST stay** — user explicitly wants tool-using agent, not direct LLM calls
- **SKILL.md must NOT be in tailor agent system prompt** — causes token overflow (1741 words)
- **SKILL.md stays in validate_ats_node.py** — that node uses it for scoring, context is shorter there
- **JSearch returns global jobs** — removed `country=eg` because Egypt has almost no listings
- **Frontend port: 5173, Backend port: 8001** — both must match api.js baseURL
