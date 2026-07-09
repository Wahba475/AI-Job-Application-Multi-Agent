from concurrent.futures import ThreadPoolExecutor
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage
from ..tools.llm_client import agent_llm, strip_think
from ..tools.tailor_tools import (
    extract_jd_keywords,
    rewrite_cv_section,
    check_ats_score,
    finalize_cv
)

# ── Configuration ──────────────────────────────────────────
# how many jobs to tailor at the same time
# 3 (not 5): each job's ReAct agent fires several tool calls, and 5 agents in
# flight burst past NVIDIA's 32-concurrent worker limit — the resulting
# 429/503 backoff sleeps cost more time than the extra parallelism saved
MAX_CONCURRENT_JOBS = 3

# ── System prompt for the ReAct agent ──────────────────────
# this tells the LLM what tools it has and in what order to use them
TAILOR_SYSTEM_PROMPT = """You are a CV tailoring specialist. Use your 4 tools in this order:

1. extract_jd_keywords(jd_text) — extract skills from job description
2. check_ats_score(cv_text, jd_text) — find gaps in current CV
3. rewrite_cv_section(...) — fix each section that has gaps
4. check_ats_score(...) — check again, if score >= 70 go to step 5
5. finalize_cv(...) — assemble final CV, output ONLY the result

HARD RULES:
- NEVER invent skills, metrics, or experience not in the original CV
- Only reword, reorder, and emphasize existing content
- Final message must be ONLY the plain text CV, no explanation"""

# ── Create the ReAct agent once (reused for every job) ─────
# this is the same as your padel bot's graph but pre-built:
# agent node → tools_condition → tool node → back to agent
_tools = [extract_jd_keywords, rewrite_cv_section, check_ats_score, finalize_cv]
_agent = create_react_agent(agent_llm, _tools)


def _extract_final_cv(messages):
    """Return the plain-text CV produced by the finalize_cv tool.

    In a ReAct run the tool's output arrives as a ToolMessage(name="finalize_cv").
    That is the clean, assembled CV — unlike the agent's final AIMessage, which
    is the model narrating its process. We scan from the end for the most recent
    finalize_cv result. Falls back to the last message with <think> stripped
    only if the tool was never called (shouldn't happen, but stay safe)."""
    for msg in reversed(messages):
        if getattr(msg, "name", None) == "finalize_cv" and getattr(msg, "content", None):
            return strip_think(msg.content).strip()
    return ""


# ── Process ONE job (this function runs inside a thread) ───
def _tailor_one_job(job, cv_text, feedback):
    """
    Takes one job and the user's CV.
    Runs the ReAct agent to tailor the CV for this specific job.
    Returns {job, cv_text} or None if it fails.
    
    This function knows nothing about other jobs.
    It runs independently in its own thread.
    """

    # if this is a retry, include feedback from the validator
    # first run: feedback is "" (empty string)
    # retry: feedback is "SCORE:55 GAPS: Docker SECTIONS: Skills"
    feedback_section = ""
    if feedback:
        feedback_section = f"\n\nPREVIOUS ATTEMPT FEEDBACK — fix these issues:\n{feedback}"

    # build the message the agent will read
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

    # try twice — if first attempt fails (rate limit, timeout), retry once
    for attempt in range(2):
        try:
            result = _agent.invoke(
                {
                    "messages": [
                        SystemMessage(content=TAILOR_SYSTEM_PROMPT),
                        HumanMessage(content=user_message),
                    ]
                },
                # safety limit: agent can loop max 30 times
                # prevents infinite tool-calling loops
                config={"recursion_limit": 30}
            )

            # The clean CV is the RETURN VALUE of the finalize_cv tool, not the
            # agent's final chat message — that message is the model narrating
            # ("I'll help you optimize...") plus reasoning/JSON, which is NOT a
            # usable CV. Pull the finalize_cv tool output from the history.
            final_cv = _extract_final_cv(result["messages"])
            if final_cv:
                print(f"  Done: {job['title']} @ {job['company']}")
                return {"job": job, "cv_text": final_cv}

            # Agent finished but never called finalize_cv (the reasoning model
            # sometimes rambles instead of using the tool on harder jobs). Retry
            # once more, then fall back below.
            print(f"  No finalize_cv output for {job['title']} @ {job['company']}, retrying...")

        except Exception as e:
            print(f"  Failed attempt {attempt + 1}/2 for {job['title']}: {e}")

    # Never drop a job to zero: deliver the candidate's ORIGINAL CV untailored.
    # It's clean, valid, honest, and downloadable — the validator will score it
    # against the job so the user still gets a real ATS number and gap list.
    print(f"  Fallback: delivering original CV for {job['title']} @ {job['company']}")
    return {"job": job, "cv_text": cv_text}


# ── The actual LangGraph node ──────────────────────────────
def tailor_cv_node(state):
    """
    Reads: state["filtered_jobs"], state["cv_text"], state["ats_feedback"]
    Writes: state["tailored_cvs"]
    
    For each job in filtered_jobs, runs the ReAct agent to tailor the CV.
    Jobs run concurrently (at the same time) using a thread pool.
    """

    # read from state
    cv_text = state["cv_text"]
    filtered_jobs = state["filtered_jobs"]
    ats_feedback = state.get("ats_feedback", {})

    print(f"\n[TAILOR] Processing {len(filtered_jobs)} job(s) concurrently...")

    # ── CONCURRENT EXECUTION ──────────────────────────────
    # 
    # Without ThreadPoolExecutor (sequential):
    #   Job 1 takes 30s → Job 2 takes 30s → Job 3 takes 30s = 90s total
    #
    # With ThreadPoolExecutor (concurrent):
    #   Job 1, 2, 3 all start at the same time = ~30s total
    #
    # ThreadPoolExecutor is the "kitchen manager"
    # max_workers is how many "chefs" (threads) work at once

    tailored_cvs = []

    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_JOBS) as pool:

        # ── SUBMIT PHASE ──────────────────────────────────
        # give each job to the pool — pool assigns it to a thread
        # pool.submit() does NOT wait — it returns immediately
        # "future" = a promise that the result will be available later

        futures = []

        for job in filtered_jobs:
            # build the feedback key for this specific job
            job_key = f"{job['company']}_{job['title']}"
            feedback = ats_feedback.get(job_key, "")

            # submit to pool — a thread starts working on this job
            future = pool.submit(_tailor_one_job, job, cv_text, feedback)

            # save the future so we can get the result later
            futures.append(future)

        # at this point, all jobs are running simultaneously
        # we haven't waited for any of them yet

        # ── COLLECT PHASE ─────────────────────────────────
        # now wait for each thread to finish and get its result
        # future.result() blocks until that specific thread is done

        for future in futures:
            try:
                result = future.result()
                if result is not None:
                    tailored_cvs.append(result)
            except Exception as e:
                print(f"  Thread failed: {e}")

    # all threads finished, all results collected

    print(f"[TAILOR] Completed: {len(tailored_cvs)} CV(s) tailored")

    # write back to state
    return {"tailored_cvs": tailored_cvs}