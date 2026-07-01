import os
import re
from Tools.llm_client import llm
from langchain_core.messages import SystemMessage, HumanMessage

_skill_path = os.path.join(os.path.dirname(__file__), "..", "Skills", "SKILL.md")
with open(_skill_path, "r", encoding="utf-8") as f:
    _ATS_SKILL = f.read()

VALIDATE_SYSTEM_PROMPT = """You are an ATS scoring specialist and CV integrity auditor embedded in an automated job application pipeline.

You have two jobs:
1. Score the tailored CV against the job description using the ATS methodology below
2. Detect fabrication — any content in the tailored CV that does not exist in the original CV

=== ATS SCORING METHODOLOGY ===
""" + _ATS_SKILL + """

=== FABRICATION DETECTION RULES ===

Compare the TAILORED CV against the ORIGINAL CV line by line.
Set FABRICATION to true if the tailored CV contains ANY of:
- Skills or technologies not mentioned in the original CV
- Project names, descriptions, or outcomes not in the original CV
- Company names, job titles, or employment dates not in the original CV
- Metrics or numbers (50k requests, 200 clients, 3x improvement) not in the original CV
- Certifications or degrees not in the original CV
- Any achievement or responsibility not derivable from the original CV

Set FABRICATION to false only if every piece of information in the tailored CV can be traced back to the original CV (reworded is fine, invented is not).

=== OUTPUT FORMAT (CRITICAL) ===

Respond with EXACTLY this format on a single line, nothing else:
SCORE:XX FABRICATION:true/false

Where:
- XX is an integer from 0 to 100
- true/false is lowercase

Example valid outputs:
SCORE:82 FABRICATION:false
SCORE:55 FABRICATION:true
SCORE:71 FABRICATION:false

No explanation. No newlines. No other text. Any other output will crash the pipeline."""


def _parse_response(text: str):
    match = re.search(r"SCORE:(\d+)\s+FABRICATION:(true|false)", text.strip(), re.IGNORECASE)
    if match:
        score      = int(match.group(1))
        fabricated = match.group(2).lower() == "true"
        return score, fabricated
    return 50, False


def validate_ats_node(state):
    tailored_cvs  = state["tailored_cvs"]
    retry_count   = state["retry_count"]
    approved_cvs  = list(state["approved_cvs"])
    original_cv   = state["cv_text"]
    ats_feedback  = dict(state.get("ats_feedback", {}))

    jobs_to_retry = []

    print(f"\n[VALIDATE] Round {retry_count + 1} — scoring {len(tailored_cvs)} CV(s)")

    for item in tailored_cvs:
        job         = item["job"]
        tailored_cv = item["cv_text"]
        job_key     = f"{job['company']}_{job['title']}"

        human_message = f"""JOB DESCRIPTION:
{job['description']}

ORIGINAL CV (ground truth — use this to detect fabrication):
{original_cv}

TAILORED CV (score this against the job description AND check for fabrication vs original):
{tailored_cv}"""

        response       = llm.invoke([
            SystemMessage(content=VALIDATE_SYSTEM_PROMPT),
            HumanMessage(content=human_message)
        ])
        score, fabricated = _parse_response(response.content)

        print(f"  {job['title']} @ {job['company']}: score={score}% fabrication={fabricated}")

        if fabricated:
            if retry_count >= 3:
                approved_cvs.append({**item, "ats_score": score})
                print(f"    → Force-approved (max retries reached, fabrication flag ignored)")
            else:
                jobs_to_retry.append(job)
                ats_feedback[job_key] = (
                    f"FABRICATION DETECTED (score: {score}%). "
                    f"The tailored CV contains invented content not present in the original CV. "
                    f"Remove ALL fabricated skills, metrics, company names, or achievements. "
                    f"Use ONLY content from the original CV — reword existing content, never invent."
                )
                print(f"    → Retry queued (fabrication)")

        elif score >= 70:
            approved_cvs.append({**item, "ats_score": score})
            print(f"    → Approved")

        else:
            if retry_count >= 3:
                approved_cvs.append({**item, "ats_score": score})
                print(f"    → Force-approved (max retries reached)")
            else:
                jobs_to_retry.append(job)
                ats_feedback[job_key] = (
                    f"ATS score was {score}% (minimum required: 70%). "
                    f"Insert more exact keywords from the job description. "
                    f"Reorder bullets so the most relevant experience appears first. "
                    f"Use ONLY content from the original CV — do not invent anything new."
                )
                print(f"    → Retry queued (score too low)")

    return {
        "approved_cvs":  approved_cvs,
        "filtered_jobs": jobs_to_retry,
        "tailored_cvs":  [],
        "retry_count":   retry_count + 1,
        "ats_feedback":  ats_feedback,
    }
