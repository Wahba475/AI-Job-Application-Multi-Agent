import re
from ..tools.llm_client import llm, strip_think
from langchain_core.messages import SystemMessage, HumanMessage

# One batched cloud call replaces N sequential local calls. Besides being
# ~10x faster, it sees the candidate's actual CV — so it only passes jobs the
# CV can honestly score well on, which is what keeps the tailor/validate
# retry loop from spinning on impossible matches (e.g. a Rust job for a
# Python-only candidate).
MAX_JOBS = 5
DESCRIPTION_SNIPPET_CHARS = 500

FILTER_SYSTEM_PROMPT = """You are a strict job-matching specialist in an automated job application pipeline.

You will receive a candidate profile (desired role, experience level, and their actual CV) and a numbered list of job postings.

Select the jobs genuinely worth applying to, judged by ALL of:
1. Title match: same role or close equivalent to the desired role.
2. Seniority match: no senior/lead/manager roles for junior candidates.
3. CV support: the candidate's CV must plausibly cover the job's core stack and requirements. If the job's primary language/stack is absent from the CV (e.g. job needs Rust, CV is Python-only), it is NOT a match — a tailored CV could never honestly pass ATS for it.
4. Internships/entry-level roles are always acceptable for intern or junior candidates.

CRITICAL OUTPUT RULES:
Respond with EXACTLY one line, nothing else:
MATCHES: 3, 7, 12
- Comma-separated indices of the matching jobs, best match first, maximum {max_jobs}.
- If nothing matches, respond exactly: MATCHES: none"""


def filter_relevance_node(state):
    jobs       = state["jobs"]
    job_title  = state["job_title"]
    experience = state["experience"]
    cv_text    = state["cv_text"]

    if not jobs:
        return {"filtered_jobs": []}

    job_lines = []
    for i, job in enumerate(jobs):
        snippet = job["description"][:DESCRIPTION_SNIPPET_CHARS].replace("\n", " ")
        job_lines.append(f"[{i}] {job['title']} @ {job['company']} ({job['employment_type']}): {snippet}")

    human_message = f"""CANDIDATE PROFILE:
- Desired role: {job_title}
- Experience level: {experience}
- CV:
{cv_text}

JOB POSTINGS:
{chr(10).join(job_lines)}

Which jobs are worth applying to?"""

    print(f"\n[FILTER] Matching {len(jobs)} job(s) against CV in one batched call...")

    try:
        response = llm.invoke([
            SystemMessage(content=FILTER_SYSTEM_PROMPT.format(max_jobs=MAX_JOBS)),
            HumanMessage(content=human_message),
        ])
        # Strip leaked reasoning first — numbers inside <think> text would
        # otherwise be misread as job indices.
        content = strip_think(response.content)
        match = re.search(r"MATCHES:\s*(.+)", content, re.IGNORECASE)
        indices = [int(m) for m in re.findall(r"\d+", match.group(1) if match else content)]
        relevant = [jobs[i] for i in indices if 0 <= i < len(jobs)]
    except Exception as e:
        print(f"[FILTER] Batched filter failed ({e}), falling back to first {MAX_JOBS} jobs")
        relevant = jobs

    print(f"[FILTER] Selected {min(len(relevant), MAX_JOBS)} job(s)")
    return {"filtered_jobs": relevant[:MAX_JOBS]}
