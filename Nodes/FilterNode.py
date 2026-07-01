from Tools.llm_client import llm
from langchain_core.messages import SystemMessage, HumanMessage

FILTER_SYSTEM_PROMPT = """You are a strict job relevance classifier embedded in an automated job application pipeline.

CANDIDATE PROFILE:
- Desired role: {job_title}
- Experience level: {experience}

YOUR TASK:
Decide whether each job posting is worth applying to for this candidate.

CLASSIFICATION RULES:
1. Title match: the job title must be the same role or a close equivalent (e.g. "Software Developer" counts for "Software Engineer", but "IT Support" does not).
2. Seniority match: do not approve senior/lead/manager roles for junior or intern candidates. Do not discard mid-level roles for junior candidates if the description mentions entry-level welcome.
3. Domain match: if the job description is clearly in an unrelated technical domain (e.g. embedded firmware when candidate wants web dev), mark not_relevant.
4. Internships and entry-level positions are always relevant for intern or junior experience levels.
5. When in doubt and the role is plausibly related, prefer relevant over not_relevant.

CRITICAL OUTPUT RULES:
- Respond with EXACTLY one word, lowercase, no punctuation, no explanation.
- The only valid outputs are: relevant   or   not_relevant
- Any other output will crash the pipeline."""


def filter_relevance_node(state):
    job_title = state["job_title"]
    experience = state["experience"]

    system_prompt = FILTER_SYSTEM_PROMPT.format(
        job_title=job_title,
        experience=experience
    )

    relevant = []

    for job in state["jobs"]:
        human_message = f"""JOB POSTING TO CLASSIFY:
Title: {job['title']}
Company: {job['company']}
Employment Type: {job['employment_type']}
Description (first 600 characters):
{job['description'][:600]}

Is this job relevant for the candidate?"""

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_message)
        ])

        verdict = response.content.strip().lower()

        if verdict == "relevant":
            relevant.append(job)

    return {"filtered_jobs": relevant}
