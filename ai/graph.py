from langgraph.graph import StateGraph, END, START
from dotenv import load_dotenv

load_dotenv()

from .state import JobAgentState
from .nodes.job_node import search_jobs_node
from .nodes.filter_node import filter_relevance_node
from .nodes.tailor_cv_node import tailor_cv_node
from .nodes.validate_ats_node import validate_ats_node
from .nodes.build_deliverable_node import build_deliverable_node


def route_after_validation(state):
    if state["filtered_jobs"]:
        return "tailor_cv"
    return "build_deliverable"


graph = StateGraph(JobAgentState)

graph.add_node("search_jobs",       search_jobs_node)
graph.add_node("filter_relevance",  filter_relevance_node)
graph.add_node("tailor_cv",         tailor_cv_node)
graph.add_node("validate_ats",      validate_ats_node)
graph.add_node("build_deliverable", build_deliverable_node)

graph.add_edge(START,               "search_jobs")
graph.add_edge("search_jobs",       "filter_relevance")
graph.add_edge("filter_relevance",  "tailor_cv")
graph.add_edge("tailor_cv",         "validate_ats")
graph.add_conditional_edges(
    "validate_ats",
    route_after_validation,
    {
        "tailor_cv":         "tailor_cv",
        "build_deliverable": "build_deliverable",
    }
)
graph.add_edge("build_deliverable", END)

pipeline = graph.compile()
