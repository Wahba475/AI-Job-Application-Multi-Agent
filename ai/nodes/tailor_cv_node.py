import time
import logging
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage
from ..tools.llm_client import AGENT_MODELS, strip_think
from ..tools.tailor_tools import (
    extract_jd_keywords,
    rewrite_cv_section,
    check_ats_score,
    finalize_cv
)

logger = logging.getLogger("applyai.tailor")

# ── Configuration ──────────────────────────────────────────
# Jobs are tailored SEQUENTIALLY, not concurrently. On free-tier LLMs, firing
# several ReAct agents at once instantly blows the token-per-minute limit, so
# every job after the first 429s and silently falls back to the ORIGINAL CV —
# which is exactly why all tailored CVs used to come out identical. Running one
# job at a time with a short gap keeps us under the rate limit so each job is
# actually tailored to its own job description.
DELAY_BETWEEN_JOBS = 3  # seconds

# ── System prompt for the ReAct agent ──────────────────────
TAILOR_SYSTEM_PROMPT = """You are a CV tailoring specialist. Use your 4 tools in this order:

1. extract_jd_keywords(jd_text) — extract skills from job description
2. check_ats_score(cv_text, jd_text) — find gaps in current CV
3. rewrite_cv_section(...) — fix each section that has gaps
4. check_ats_score(...) — check again, if score >= 70 go to step 5
5. finalize_cv(...) — assemble final CV, output ONLY the result

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

    Runs jobs one at a time with a short delay to stay under free-tier rate
    limits — the fix for 'all tailored CVs look identical'.
    """
    cv_text = state["cv_text"]
    filtered_jobs = state["filtered_jobs"]
    ats_feedback = state.get("ats_feedback", {})

    print(f"\n[TAILOR] Processing {len(filtered_jobs)} job(s) sequentially...")

    tailored_cvs = []
    for i, job in enumerate(filtered_jobs):
        job_key = f"{job['company']}_{job['title']}"
        feedback = ats_feedback.get(job_key, "")
        tailored_cvs.append(_tailor_one_job(job, cv_text, feedback))

        # Space out calls to stay under the token-per-minute ceiling.
        if i < len(filtered_jobs) - 1:
            time.sleep(DELAY_BETWEEN_JOBS)

    n_tailored = sum(1 for r in tailored_cvs if r.get("tailored"))
    print(f"[TAILOR] Completed: {n_tailored}/{len(tailored_cvs)} actually tailored "
          f"({len(tailored_cvs) - n_tailored} original-CV fallback)")

    return {"tailored_cvs": tailored_cvs}
