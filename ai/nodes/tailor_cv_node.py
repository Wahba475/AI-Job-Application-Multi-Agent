import os
import logging
from concurrent.futures import ThreadPoolExecutor
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage
from ..tools.llm_client import AGENT_MODELS, strip_think, PROVIDER_ORDER
from ..tools.tailor_tools import (
    extract_jd_keywords,
    rewrite_cv_section,
    check_ats_score,
    finalize_cv
)

logger = logging.getLogger("applyai.tailor")

# ── Concurrency ────────────────────────────────────────────
# On a high-TPM provider (OpenAI: 200k TPM) we tailor jobs in parallel for speed.
# On a free provider (Groq: 8k TPM) parallel agents instantly blow the token
# limit, so every job but the first 429s and falls back to the ORIGINAL CV —
# which is what made all tailored CVs look identical. So: parallel when the
# primary provider is OpenAI, otherwise 1-at-a-time.
#   TAILOR_CONCURRENCY env overrides the auto choice.
_auto = 4 if PROVIDER_ORDER and PROVIDER_ORDER[0] == "openai" else 1
MAX_CONCURRENT_JOBS = int(os.getenv("TAILOR_CONCURRENCY", str(_auto)))

# ── System prompt for the ReAct agent ──────────────────────
TAILOR_SYSTEM_PROMPT = """You are a CV tailoring specialist. Work efficiently in this order:

1. extract_jd_keywords(jd_text) — extract the skills this job wants
2. rewrite_cv_section(...) — rewrite each section that has gaps, weaving in the
   job's keywords wherever the original CV honestly supports them
3. finalize_cv(...) — assemble the final CV and output ONLY its result

(A separate validator scores the result, so you do NOT need to call
check_ats_score yourself unless you are unsure a rewrite helped.)

HARD RULES:
- NEVER invent skills, metrics, or experience not in the original CV
- Only reword, reorder, and emphasize existing content
- Emphasize the skills and keywords THIS specific job asks for
- Final message must be ONLY the plain text CV, no explanation"""

# One ReAct agent per provider (best first). A fallback-wrapped runnable can't
# be used by create_react_agent (needs .bind_tools), so we try agents in order.
_tools = [extract_jd_keywords, rewrite_cv_section, check_ats_score, finalize_cv]
_agents = [create_react_agent(model, _tools) for model in AGENT_MODELS]


def _extract_final_cv(messages):
    """Return the plain-text CV produced by the finalize_cv tool (a ToolMessage
    named 'finalize_cv') — not the agent's chatty final AIMessage."""
    for msg in reversed(messages):
        if getattr(msg, "name", None) == "finalize_cv" and getattr(msg, "content", None):
            return strip_think(msg.content).strip()
    return ""


def _tailor_one_job(job, cv_text, feedback):
    """Tailor the CV for ONE job. Returns {job, cv_text, tailored: bool}.

    tailored=True  → the ReAct agent produced a job-specific CV.
    tailored=False → every provider failed; we return the ORIGINAL CV as a
                     safe fallback and log a WARNING so it's visible.
    """
    feedback_section = ""
    if feedback:
        feedback_section = f"\n\nPREVIOUS ATTEMPT FEEDBACK — fix these issues:\n{feedback}"

    user_message = f"""Tailor this CV for the job posting below.

JOB POSTING:
Title: {job['title']}
Company: {job['company']}
Location: {job['location']}
Employment Type: {job['employment_type']}
Full Description:
{job['description']}

CANDIDATE'S ORIGINAL CV:
{cv_text}{feedback_section}

Follow your 5-step process. Call finalize_cv last."""

    # Diagnostic: confirm each job really gets its OWN job description.
    jd_preview = (job.get("description") or "").replace("\n", " ")[:100]
    logger.info("TAILOR-IN  | %s @ %s | JD[:100]=%r",
                job["title"][:40], job["company"][:25], jd_preview)

    messages = {"messages": [
        SystemMessage(content=TAILOR_SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]}

    # Try each provider's agent in order; first success wins.
    for idx, agent in enumerate(_agents):
        try:
            result = agent.invoke(messages, config={"recursion_limit": 30})
            final_cv = _extract_final_cv(result["messages"])
            if final_cv:
                logger.info("TAILOR-OUT | %s | provider=%d | CV[:200]=%r",
                            job["title"][:40], idx, final_cv[:200])
                return {"job": job, "cv_text": final_cv, "tailored": True}
            logger.warning("No finalize_cv from provider %d for %s — trying next",
                           idx, job["title"][:40])
        except Exception as e:
            logger.warning("Provider %d failed for %s: %s", idx, job["title"][:40], e)

    # All providers failed → original CV fallback (loud warning so it's visible).
    logger.warning("FALLBACK (untailored original CV) for %s @ %s — all providers failed",
                   job["title"][:40], job["company"][:25])
    return {"job": job, "cv_text": cv_text, "tailored": False}


def tailor_cv_node(state):
    """Reads filtered_jobs / cv_text / ats_feedback; writes tailored_cvs.

    Tailors jobs in parallel on a high-TPM provider (fast), or one-at-a-time on
    a free provider to avoid the throttle that made CVs fall back to the
    original. Each job always gets its OWN job description → distinct CVs.
    """
    cv_text = state["cv_text"]
    filtered_jobs = state["filtered_jobs"]
    ats_feedback = state.get("ats_feedback", {})

    workers = max(1, min(MAX_CONCURRENT_JOBS, len(filtered_jobs) or 1))
    print(f"\n[TAILOR] Processing {len(filtered_jobs)} job(s), concurrency={workers}...")

    def run(job):
        job_key = f"{job['company']}_{job['title']}"
        return _tailor_one_job(job, cv_text, ats_feedback.get(job_key, ""))

    with ThreadPoolExecutor(max_workers=workers) as pool:
        tailored_cvs = list(pool.map(run, filtered_jobs))

    n_tailored = sum(1 for r in tailored_cvs if r.get("tailored"))
    print(f"[TAILOR] Completed: {n_tailored}/{len(tailored_cvs)} actually tailored "
          f"({len(tailored_cvs) - n_tailored} original-CV fallback)")

    return {"tailored_cvs": tailored_cvs}
