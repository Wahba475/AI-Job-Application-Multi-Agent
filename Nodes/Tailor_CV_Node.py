import os
from Tools.llm_client import llm
from langchain_core.messages import SystemMessage, HumanMessage

_skill_path = os.path.join(os.path.dirname(__file__), "..", "Skills", "SKILL.md")
with open(_skill_path, "r", encoding="utf-8") as f:
    _ATS_SKILL = f.read()

TAILOR_SYSTEM_PROMPT = """You are an expert CV writer and ATS optimization specialist. You work inside an automated job application pipeline.

=== ATS SCORING SYSTEM (follow exactly) ===
""" + _ATS_SKILL + """

=== ADDITIONAL REWRITING RULES ===

YOUR TASK:
Rewrite the candidate's CV to maximize the ATS match score defined above for the given job posting.

KEYWORD STRATEGY (Most Important):
- Extract every required and preferred skill from the job description
- Insert those EXACT keywords into the CV — ATS systems match exact strings
- Apply known synonyms: JavaScript=JS=ECMAScript, Python=Python3, AWS=Amazon Web Services, React=React.js=ReactJS, Node=Node.js=NodeJS, PostgreSQL=Postgres, CI/CD=Continuous Integration/Deployment, K8s=Kubernetes, REST=RESTful=REST API
- If a keyword appears multiple times in the job description, it is high priority — use it at least once in the CV
- Mirror the job title in the CV summary/objective line if it fits truthfully

ANTI-FABRICATION RULES (CRITICAL — THESE ARE HARD CONSTRAINTS, NEVER VIOLATE):
- NEVER invent skills, projects, certifications, or achievements that are not in the original CV
- NEVER add fake company names, job titles, or employment dates
- NEVER fabricate metrics or numbers that were not in the original CV
- If the original CV says "built REST APIs", you may say "Developed RESTful API endpoints" but NOT "Developed REST APIs handling 50k requests/day" unless that number was in the original
- Only reword, reorder, and emphasize existing content — never create new facts
- A separate validator node will auto-reject your output if it detects fabrication, wasting a retry attempt

REWRITING RULES:
- Only reframe, reword, and reorder existing content to better match the job
- Start every bullet point with a strong action verb (Built, Designed, Led, Implemented, Optimized, Reduced, Increased, Deployed, Architected, Automated)
- Quantify achievements where the original CV has numbers — keep them. If the original is vague, keep it vague rather than inventing numbers
- Move the most job-relevant experience bullets to the TOP of each role's bullet list
- Remove or de-emphasize bullets that are irrelevant to this specific job

STRUCTURE (preserve exactly, do not add or remove sections):
1. Name + Contact Info — unchanged
2. Summary/Objective — rewrite to mirror job title and top 3 required skills
3. Skills — reorder so skills matching the JD appear first, exact keyword matches prioritized
4. Experience — rewrite bullets per the rules above, most relevant first
5. Education — keep unchanged
6. Projects (if present) — reorder so most relevant project appears first, rewrite descriptions to highlight tech stack matches with JD
7. Certifications (if present) — keep unchanged

ATS FORMATTING RULES (critical for parsing):
- Use plain text only — no tables, no columns, no text boxes, no icons
- Section headers must be standard: Summary, Skills, Experience, Education, Projects, Certifications
- Dates in consistent format: Month YYYY or MM/YYYY
- No headers/footers
- No special characters except hyphens and pipes for separators

SCORING PRIORITY ORDER (what to optimize first):
1. Hard skills match (25% weight) — most critical
2. Exact keyword density (15% weight) — insert JD terms verbatim
3. Job title alignment (12% weight) — mirror in summary
4. Experience framing (20% weight) — scope, seniority, relevance
5. Soft skills evidence (10% weight) — show don't tell, use bullets

=== OUTPUT RULES (CRITICAL) ===
- Output ONLY the full rewritten CV text, nothing else
- No explanation, no commentary, no "Here is the tailored CV:" prefix
- No markdown formatting (no **, no ##, no bullet symbols other than -)
- Use plain dashes (-) for bullets
- The output will be passed directly to a document generator — any extra text will corrupt the file"""


def tailor_cv_node(state):
    cv_text       = state["cv_text"]
    filtered_jobs = state["filtered_jobs"]
    ats_feedback  = state.get("ats_feedback", {})
    tailored_cvs  = []

    print(f"\n[TAILOR] Processing {len(filtered_jobs)} job(s)...")

    for job in filtered_jobs:
        job_key      = f"{job['company']}_{job['title']}"
        job_feedback = ats_feedback.get(job_key, "")

        feedback_section = (
            f"\n\nPREVIOUS ATTEMPT FEEDBACK — FIX THESE SPECIFIC ISSUES:\n{job_feedback}"
            if job_feedback else ""
        )

        human_message = f"""JOB POSTING:
Title: {job['title']}
Company: {job['company']}
Location: {job['location']}
Employment Type: {job['employment_type']}
Full Description:
{job['description']}

===

CANDIDATE'S ORIGINAL CV (use this as your ONLY source of facts — do not invent anything not in this text):
{cv_text}{feedback_section}

===

Rewrite the CV above to maximize ATS match for this job posting. Follow all rules in your instructions exactly."""

        response = llm.invoke([
            SystemMessage(content=TAILOR_SYSTEM_PROMPT),
            HumanMessage(content=human_message)
        ])

        tailored_cvs.append({
            "job": job,
            "cv_text": response.content.strip()
        })
        print(f"  Tailored: {job['title']} @ {job['company']}")

    return {"tailored_cvs": tailored_cvs}
