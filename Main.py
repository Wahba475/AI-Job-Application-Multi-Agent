from langgraph.graph import StateGraph, END, START
from dotenv import load_dotenv

load_dotenv()

from state import JobAgentState
from Nodes.JobNode import search_jobs_node
from Nodes.FilterNode import filter_relevance_node
from Nodes.Tailor_CV_Node import tailor_cv_node
from Nodes.Validate_ATS_Node import validate_ats_node
from Nodes.Build_Deliverable_Node import build_deliverable_node


def route_after_validation(state):
    if state["filtered_jobs"]:
        return "tailor_cv"
    return "build_deliverable"


graph = StateGraph(JobAgentState)

graph.add_node("search_jobs",      search_jobs_node)
graph.add_node("filter_relevance", filter_relevance_node)
graph.add_node("tailor_cv",        tailor_cv_node)
graph.add_node("validate_ats",     validate_ats_node)
graph.add_node("build_deliverable", build_deliverable_node)

graph.add_edge(START,              "search_jobs")
graph.add_edge("search_jobs",      "filter_relevance")
graph.add_edge("filter_relevance", "tailor_cv")
graph.add_edge("tailor_cv",        "validate_ats")
graph.add_conditional_edges(
    "validate_ats",
    route_after_validation,
    {
        "tailor_cv":        "tailor_cv",
        "build_deliverable": "build_deliverable",
    }
)
graph.add_edge("build_deliverable", END)

pipeline = graph.compile()


if __name__ == "__main__":
    print("=== Job Application Agent ===\n")

    job_title  = input("Job title: ").strip()
    location   = input("Location: ").strip()
    experience = input("Experience level (Junior / Senior / Intern): ").strip()

    cv_path = input("CV file path (leave blank to paste text): ").strip()
    if cv_path:
        with open(cv_path, "r", encoding="utf-8") as f:
            cv_text = f.read()
        print(f"CV loaded ({len(cv_text)} chars)\n")
    else:
        print("Paste your CV. Type END on a new line when done:")
        lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
        cv_text = "\n".join(lines)

    result = pipeline.invoke({
        "job_title":    job_title,
        "location":     location,
        "experience":   experience,
        "cv_text":      cv_text,
        "jobs":         [],
        "filtered_jobs": [],
        "tailored_cvs": [],
        "approved_cvs": [],
        "retry_count":  0,
        "ats_feedback": {},
    })

    print(f"\n=== Pipeline Summary ===")
    print(f"  Jobs found:      {len(result['jobs'])}")
    print(f"  After filter:    {len(result['approved_cvs'])} relevant")
    print(f"  CVs approved:    {len(result['approved_cvs'])}")
    print(f"  Retry rounds:    {result['retry_count']}")
