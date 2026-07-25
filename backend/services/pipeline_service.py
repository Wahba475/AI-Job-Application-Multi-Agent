from ai.graph import pipeline


def run_job_pipeline(run_id: str, job_title: str, location: str,
                     experience: str, cv_text: str, on_step=None) -> dict:
    """Run the LangGraph pipeline for one request and return the raw results.

    on_step(node_name) is called as each node finishes, so the controller can
    surface live progress (search → filter → tailor → validate → build).

    Returns job_results (best-fit first) carrying each CV's local path + text +
    tailored flag. The controller persists these to Supabase and shapes the
    frontend/history payload.
    """
    initial = {
        "run_id":       run_id,
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
        "job_results":  [],
    }

    # Stream node-by-node so we can report progress; merge updates into state.
    result = dict(initial)
    for chunk in pipeline.stream(initial, config={"recursion_limit": 12},
                                 stream_mode="updates"):
        for node_name, update in chunk.items():
            if on_step:
                try:
                    on_step(node_name)
                except Exception:
                    pass
            if isinstance(update, dict):
                result.update(update)

    # Best fit first — strongest matches at the top.
    ranked = sorted(
        result.get("job_results", []),
        key=lambda j: j.get("ats_score", 0) if isinstance(j.get("ats_score"), (int, float)) else 0,
        reverse=True,
    )

    return {
        "run_id":         run_id,
        "total_jobs":     len(result["jobs"]),
        "approved_count": len(ranked),
        "retry_rounds":   result["retry_count"],
        "job_results":    ranked,
    }
