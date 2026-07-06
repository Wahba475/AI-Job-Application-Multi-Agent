import time
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from .llm_client import llm


def _invoke(messages, retries=4):
    for i in range(retries):
        try:
            return llm.invoke(messages)
        except Exception as e:
            if "429" in str(e) and i < retries - 1:
                wait = 5 * (i + 1)
                print(f"[TOOL] Rate limit, retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise


@tool
def extract_jd_keywords(jd_text: str) -> str:
    """Extract required and preferred skills and keywords from a job description.
    Call this FIRST before rewriting any CV section.
    Returns structured keyword lists the CV must include to pass ATS.

    Args:
        jd_text: The full job description text.
    """
    response = _invoke([
        SystemMessage(content="""Extract all technical skills, tools, frameworks, and keywords from this job description.
Classify each as REQUIRED or PREFERRED.
Return EXACTLY this format — no other text:
REQUIRED: Python, FastAPI, PostgreSQL, Docker
PREFERRED: Kubernetes, Redis, AWS
TITLE_KEYWORDS: Backend Engineer, Software Engineer"""),
        HumanMessage(content=jd_text)
    ])
    return response.content.strip()


@tool
def rewrite_cv_section(
    section_name: str,
    current_content: str,
    keywords_to_add: str,
    original_content: str
) -> str:
    """Rewrite ONE section of the CV to include target keywords without fabricating any content.
    Uses only the original_content as ground truth — never invents new facts.
    Call once per section that has keyword gaps.

    Args:
        section_name: The section to rewrite — e.g. Skills, Experience, Projects, Summary.
        current_content: The current text of this section in the working CV draft.
        keywords_to_add: Comma-separated keywords this section should include.
        original_content: The original unmodified content of this section from the candidate's real CV.
    """
    response = _invoke([
        SystemMessage(content=f"""You are rewriting the {section_name} section of a CV to improve ATS keyword match.

ANTI-FABRICATION RULES — NEVER VIOLATE:
- You may ONLY use content present in the ORIGINAL section provided below
- You may reword, reorder, and restructure bullets — never invent skills, metrics, or roles
- If a target keyword has no basis in the original content, do not add it
- NEVER add numbers (50k requests, 3x improvement) that were not in the original
- Output ONLY the rewritten section text — no labels, no explanations

ORIGINAL {section_name.upper()} (ground truth):
{original_content}"""),
        HumanMessage(content=f"Insert these keywords where the original content justifies it:\n{keywords_to_add}\n\nCurrent draft of this section:\n{current_content}")
    ])
    return response.content.strip()


@tool
def check_ats_score(cv_text: str, jd_text: str) -> str:
    """Score the current CV draft against the job description and identify remaining gaps.
    Call this after rewriting sections to decide if more improvement is needed.
    Returns the score and which sections still need work.

    Args:
        cv_text: The current assembled CV text (can be partial — just the sections rewritten so far).
        jd_text: The full job description text to score against.
    """
    response = _invoke([
        SystemMessage(content="""You are a strict ATS scoring system. Score the CV against the job description.

Return EXACTLY this format on 3 lines, nothing else:
SCORE:XX
GAPS: comma-separated missing high-priority keywords, or none
SECTIONS_TO_IMPROVE: comma-separated section names that still need work, or none"""),
        HumanMessage(content=f"JOB DESCRIPTION:\n{jd_text}\n\nCV:\n{cv_text}")
    ])
    return response.content.strip()


@tool
def finalize_cv(
    header: str,
    summary: str,
    skills: str,
    experience: str,
    education: str,
    projects: str = "",
    certifications: str = ""
) -> str:
    """Assemble all rewritten CV sections into the final plain-text CV.
    Call this LAST — only when the ATS score is >= 70 or after 3 rewrite attempts.
    Your job is done after calling this. Output the result as your final answer.

    Args:
        header: Candidate name and contact info — copy unchanged from original CV.
        summary: Rewritten summary or objective section.
        skills: Rewritten skills section.
        experience: Rewritten experience section.
        education: Education section — copy unchanged from original CV.
        projects: Rewritten projects section — leave empty string if not present in original CV.
        certifications: Certifications section — copy unchanged from original CV, or empty string.
    """
    sections = [
        header,
        "Summary\n" + summary,
        "Skills\n" + skills,
        "Experience\n" + experience,
        "Education\n" + education,
    ]
    if projects.strip():
        sections.append("Projects\n" + projects)
    if certifications.strip():
        sections.append("Certifications\n" + certifications)
    return "\n\n".join(sections)
