from typing import TypedDict


class JobAgentState(TypedDict):
    job_title: str
    location: str
    experience: str
    cv_text: str
    jobs: list[dict]
    filtered_jobs: list[dict]
    tailored_cvs: list[dict]
    approved_cvs: list[dict]
    retry_count: int
    ats_feedback: dict
