from ai.graph import pipeline


def run_job_pipeline(job_title: str, location: str, experience: str, cv_text: str) -> dict:
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
                "cv_text":     item.get("cv_text", ""),
                "cv_filename": f"CV_{item['job']['company']}_{item['job']['title']}.docx".replace(" ", "_"),
            }
            for item in result["approved_cvs"]
        ],
        "spreadsheet_download": "jobs.xlsx"
    }
