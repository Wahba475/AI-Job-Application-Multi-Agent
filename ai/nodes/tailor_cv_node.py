from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage
from ..tools.llm_client import agent_llm
from ..tools.tailor_tools import extract_jd_keywords, rewrite_cv_section, check_ats_score, finalize_cv

TAILOR_AGENT_SYSTEM_PROMPT = """You are a CV tailoring specialist. Tailor the candidate's CV to maximize ATS keyword match for the job posting. Use your 4 tools in this exact order:

1. extract_jd_keywords(jd_text) — call once with the full job description
2. check_ats_score(cv_text, jd_text) — call with original CV to find gaps
3. rewrite_cv_section(section_name, current_content, keywords_to_add, original_content) — call once per section with gaps; use original content as ground truth
4. check_ats_score(assembled_sections, jd_text) — call again; if score >= 70 go to step 5, else repeat step 3
5. finalize_cv(header, summary, skills, experience, education, projects, certifications) — call last to assemble final CV

HARD RULES:
- NEVER invent skills, technologies, metrics, dates, companies, or job titles not in the original CV
- Only reword, reorder, and emphasize existing content
- Your final message must be ONLY the plain text from finalize_cv — no explanation, no preamble"""

_tailor_tools = [extract_jd_keywords, rewrite_cv_section, check_ats_score, finalize_cv]
_tailor_agent = create_react_agent(agent_llm, _tailor_tools)


def tailor_cv_node(state):
    cv_text       = state["cv_text"]
    filtered_jobs = state["filtered_jobs"]
    ats_feedback  = state.get("ats_feedback", {})
    tailored_cvs  = []

    print(f"\n[TAILOR] Processing {len(filtered_jobs)} job(s) with agent...")

    for job in filtered_jobs:
        job_key      = f"{job['company']}_{job['title']}"
        job_feedback = ats_feedback.get(job_key, "")

        feedback_section = (
            f"\n\nPREVIOUS ATTEMPT FEEDBACK — fix these specific issues:\n{job_feedback}"
            if job_feedback else ""
        )

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

Follow your 5-step process. Call finalize_cv last and output its result as your final message."""

        result = _tailor_agent.invoke(
            {
                "messages": [
                    SystemMessage(content=TAILOR_AGENT_SYSTEM_PROMPT),
                    HumanMessage(content=user_message),
                ]
            },
            config={"recursion_limit": 30}
        )

        final_cv = result["messages"][-1].content.strip()
        tailored_cvs.append({"job": job, "cv_text": final_cv})
        print(f"  Done: {job['title']} @ {job['company']}")

    return {"tailored_cvs": tailored_cvs}
