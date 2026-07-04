import os
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage
from Tools.llm_client import llm
from Tools.tailor_tools import extract_jd_keywords, rewrite_cv_section, check_ats_score, finalize_cv

_skill_path = os.path.join(os.path.dirname(__file__), "..", "Skills", "SKILL.md")
with open(_skill_path, "r", encoding="utf-8") as f:
    _ATS_SKILL = f.read()

TAILOR_AGENT_SYSTEM_PROMPT = """You are an expert CV tailoring specialist embedded in an automated job application pipeline.

Your job is to tailor a candidate's CV to maximize its ATS match score for a specific job posting.
You have 4 tools. Use them in order.

=== ATS SCORING SYSTEM (follow these weights) ===
""" + _ATS_SKILL + """

=== YOUR PROCESS (follow exactly) ===

STEP 1 — extract_jd_keywords(jd_text)
  Call this once with the full job description.
  This tells you which keywords must appear in the CV.

STEP 2 — check_ats_score(cv_text, jd_text)
  Call with the original CV and job description.
  This shows you where the biggest gaps are and which sections to improve.

STEP 3 — rewrite_cv_section(section_name, current_content, keywords_to_add, original_content)
  Call once per section that has keyword gaps (Summary, Skills, Experience, Projects).
  Pass the ORIGINAL section content as original_content — this prevents fabrication.
  You may call this tool multiple times (one per section that needs work).

STEP 4 — check_ats_score(assembled_sections, jd_text)
  Call again with the updated sections assembled together.
  If score >= 70, proceed to Step 5.
  If score < 70 and you have not yet done 3 rewrite rounds, go back to Step 3 for remaining gaps.

STEP 5 — finalize_cv(header, summary, skills, experience, education, projects, certifications)
  Call this once to assemble the final CV.
  After calling finalize_cv, output its return value as your FINAL MESSAGE — nothing else.

=== HARD CONSTRAINTS ===

NEVER invent skills, technologies, projects, metrics, or dates not in the original CV.
NEVER add numbers (requests/day, team size, revenue) that were not in the original CV.
NEVER add company names or job titles that were not in the original CV.
Only reword, reorder, and emphasize existing content.

=== OUTPUT RULE ===
Your final message must be ONLY the plain text CV returned by finalize_cv.
No explanation. No "Here is the tailored CV:". Just the CV text.
The output goes directly into a document generator — any extra text corrupts the file."""

_tailor_tools = [extract_jd_keywords, rewrite_cv_section, check_ats_score, finalize_cv]
_tailor_agent = create_react_agent(llm, _tailor_tools)


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
