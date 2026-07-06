from ..tools.search_job import search_jobs
from ..state import JobAgentState


def search_jobs_node(state: JobAgentState):
    jobs = search_jobs(state["job_title"], state["location"], state["experience"])
    return {"jobs": jobs}
