import re
import time
from concurrent.futures import ThreadPoolExecutor
from ..tools.llm_client import llm, strip_think
from langchain_core.messages import SystemMessage, HumanMessage

# Score CVs concurrently — they're independent of each other. Kept modest to
# stay under the NVIDIA free-tier concurrency limit alongside other calls.
MAX_CONCURRENT_SCORING = 3

# No external retry round. The ReAct tailor agent already self-optimizes
# internally (it scores its own draft and rewrites weak sections before
# finalizing), so a second full tailor+validate pass roughly DOUBLES runtime
# while almost never crossing the 70% bar in practice (a well-matched CV
# already passes on the first try; a mismatched one never converges honestly).
# Instead we score once and deliver every CV with its honest score + the list
# of missing keywords, which is the useful, truthful outcome for the user.
MAX_RETRY_ROUNDS = 0

# Condensed scoring rubric — replaces the 1741-word SKILL.md that was being
# resent on every single scoring call.
VALIDATE_SYSTEM_PROMPT = """You are an ATS scoring specialist and CV integrity auditor.

=== SCORING RUBRIC (0-100) ===
- Keyword match (50 pts): fraction of the job description's required skills/tools/technologies that appear in the CV. Exact or clear-synonym matches count.
- Title alignment (15 pts): CV's current/recent titles vs the job title.
- Experience relevance (20 pts): how directly the CV's work history maps to the job's core responsibilities.
- Education & certifications (10 pts): meets stated requirements.
- Structure (5 pts): standard sections present (summary, skills, experience, education).

=== FABRICATION CHECK ===
Compare the TAILORED CV against the ORIGINAL CV. FABRICATION is true if the tailored CV contains ANY skill, technology, project, employer, title, date, metric, certification, or achievement that is not present in (or directly derivable from) the original CV. Rewording is fine; inventing is not.

=== GAPS ===
List AT MOST the 8 single most important skills/technologies/qualifications from the job description that are missing from the tailored CV. Each gap must be a short keyword or phrase (1-4 words), NOT a sentence, NOT copied job-description prose.

=== OUTPUT FORMAT (CRITICAL) ===
Respond with EXACTLY two lines, nothing else:
SCORE:XX FABRICATION:true/false
GAPS: keyword1, keyword2, keyword3

- XX is an integer 0-100. true/false lowercase.
- Maximum 8 comma-separated gap keywords. If nothing is missing, write: GAPS: none
No explanation. No other text."""

# Hard cap so a chatty model can never dump the whole JD into the UI.
MAX_GAPS = 8


def _parse_response(text: str):
    text = text.strip()
    match = re.search(r"SCORE:\s*(\d+)\s+FABRICATION:\s*(true|false)", text, re.IGNORECASE)
    score, fabricated = (int(match.group(1)), match.group(2).lower() == "true") if match else (50, False)

    gaps_match = re.search(r"GAPS:\s*(.+)", text, re.IGNORECASE)
    gaps = gaps_match.group(1).strip() if gaps_match else ""
    if gaps.lower() == "none":
        gaps = ""
    else:
        # Hard cap: keep only the first MAX_GAPS keywords, drop overly long
        # items (sentences / copied JD prose the model sometimes emits).
        items = [g.strip() for g in gaps.split(",") if g.strip()]
        items = [g for g in items if len(g.split()) <= 5][:MAX_GAPS]
        gaps = ", ".join(items)
    return score, fabricated, gaps


def _score_one(item, original_cv):
    job         = item["job"]
    tailored_cv = item["cv_text"]

    human_message = f"""JOB DESCRIPTION:
{job['description']}

ORIGINAL CV (ground truth for fabrication check):
{original_cv}

TAILORED CV (score against the job description AND check for fabrication):
{tailored_cv}"""

    # Retry transient errors (429 rate limit / 503 congestion on the shared
    # free endpoint); one flaky call must never take down the whole pipeline.
    last_error = None
    for attempt in range(3):
        try:
            response = llm.invoke([
                SystemMessage(content=VALIDATE_SYSTEM_PROMPT),
                HumanMessage(content=human_message)
            ])
            score, fabricated, gaps = _parse_response(strip_think(response.content))
            print(f"  {job['title']} @ {job['company']}: score={score}% fabrication={fabricated}")
            return item, score, fabricated, gaps
        except Exception as e:
            last_error = e
            if any(code in str(e) for code in ("429", "503", "ResourceExhausted")) and attempt < 2:
                wait = 5 * (attempt + 1)
                print(f"  [VALIDATE] Transient error for {job['title']}, retrying in {wait}s...")
                time.sleep(wait)
            else:
                break

    # Scoring itself failed — deliver the CV with a neutral score rather than
    # crashing or silently dropping the job the user paid tokens to tailor.
    print(f"  [VALIDATE] Scoring failed for {job['title']} @ {job['company']}: {last_error}")
    return item, 50, False, ""


def validate_ats_node(state):
    tailored_cvs  = state["tailored_cvs"]
    retry_count   = state["retry_count"]
    approved_cvs  = list(state["approved_cvs"])
    original_cv   = state["cv_text"]
    ats_feedback  = dict(state.get("ats_feedback", {}))

    jobs_to_retry = []

    print(f"\n[VALIDATE] Round {retry_count + 1} — scoring {len(tailored_cvs)} CV(s) concurrently")

    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_SCORING) as pool:
        results = list(pool.map(lambda item: _score_one(item, original_cv), tailored_cvs))

    for item, score, fabricated, gaps in results:
        job     = item["job"]
        job_key = f"{job['company']}_{job['title']}"
        out_of_retries = retry_count >= MAX_RETRY_ROUNDS

        if not fabricated and score >= 70:
            approved_cvs.append({**item, "ats_score": score, "gaps": gaps})
            print(f"    -> Approved")

        elif out_of_retries:
            # Deliver with the honest score and what's missing — never loop
            # forever, never fabricate to force the number up.
            approved_cvs.append({**item, "ats_score": score, "gaps": gaps})
            print(f"    -> Delivered with honest score (max retries reached)")

        elif fabricated:
            jobs_to_retry.append(job)
            ats_feedback[job_key] = (
                f"FABRICATION DETECTED (score: {score}%). "
                f"The tailored CV contains invented content not present in the original CV. "
                f"Remove ALL fabricated skills, metrics, company names, or achievements. "
                f"Use ONLY content from the original CV — reword existing content, never invent."
            )
            print(f"    -> Retry queued (fabrication)")

        else:
            jobs_to_retry.append(job)
            ats_feedback[job_key] = (
                f"ATS score was {score}% (minimum required: 70%). Missing keywords: {gaps or 'unknown'}. "
                f"Insert these exact keywords where the original CV justifies them. "
                f"Reorder bullets so the most relevant experience appears first. "
                f"Use ONLY content from the original CV — do not invent anything new."
            )
            print(f"    -> Retry queued (score too low)")

    return {
        "approved_cvs":  approved_cvs,
        "filtered_jobs": jobs_to_retry,
        "tailored_cvs":  [],
        "retry_count":   retry_count + 1,
        "ats_feedback":  ats_feedback,
    }
