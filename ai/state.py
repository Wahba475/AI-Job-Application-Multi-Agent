from typing import TypedDict


class JobAgentState(TypedDict):
    run_id: str            # unique per run; scopes output files + storage paths
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
    job_results: list[dict]  # built by build_deliverable_node for the controller
