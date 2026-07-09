from ai.graph import pipeline
from ai.nodes.build_deliverable_node import cv_filename_for


def run_job_pipeline(job_title: str, location: str, experience: str, cv_text: str) -> dict:
    result = pipeline.invoke(
        {
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
        },
        # Safety net: the graph is acyclic in normal operation, but this
        # guarantees it can never hang — it errors cleanly instead of looping.
        config={"recursion_limit": 12},
    )

    # Best fit first — the user sees their strongest matches at the top.
    ranked = sorted(
        result["approved_cvs"],
        key=lambda item: item.get("ats_score", 0),
        reverse=True,
    )

    return {
        "total_jobs":     len(result["jobs"]),
        "approved_count": len(result["approved_cvs"]),
        "retry_rounds":   result["retry_count"],
        "jobs": [
            {
                "title":       item["job"]["title"],
                "company":     item["job"]["company"],
                "location":    item["job"]["location"],
                "type":        item["job"].get("employment_type", ""),
                "apply_link":  item["job"]["apply_link"],
                "ats_score":   item.get("ats_score", 0),
                "gaps":        item.get("gaps", ""),
                "cv_text":     item.get("cv_text", ""),
                "cv_filename": cv_filename_for(item["job"]),
            }
            for item in ranked
        ],
        "spreadsheet_download": "jobs.xlsx"
    }
