from Tools.Search_Job_Node import search_jobs
from state import JobAgentState


def search_jobs_node(state: JobAgentState):
    """
    Search for jobs based on the job title, location, and experience level.
    Args:
        state (JobAgentState): The current state of the agent.

    Returns:
        JobAgentState: The updated state with the search results.
    """
    jobs = search_jobs(state["job_title"], state["location"], state["experience"])
    return {"jobs": jobs}