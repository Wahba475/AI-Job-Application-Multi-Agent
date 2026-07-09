import re
import requests
import os
from dotenv import load_dotenv

load_dotenv()


def search_jobs(job_title: str, location: str, experience: str) -> list:
    url = "https://jsearch.p.rapidapi.com/search-v2"

    headers = {
        "X-RapidAPI-Key": os.getenv("JSearch_API"),
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }

    # Strip the "(0-2 years)" suffix — the parenthetical/en-dash text confuses
    # JSearch's query parser and tanks result counts (e.g. "Mid Level (3–5
    # years)" -> "Mid Level").
    experience_label = re.sub(r"\s*\([^)]*\)\s*$", "", experience).strip()

    # JSearch's underlying index (Google for Jobs) has very thin direct
    # coverage in Egypt — a hard `country=eg` filter returns almost nothing.
    # Broadening to remote roles as well, since those are reachable from
    # Egypt and JSearch actually has listings for them.
    search_location = f"{location} OR Remote" if "egypt" in location.lower() else location

    params = {
        "query": f"{job_title} {experience_label} in {search_location}",
        "num_pages": "2",
        "date_posted": "month",
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    raw = data.get("data", {})
    items = raw.get("jobs", []) if isinstance(raw, dict) else raw
    print(f"[JSearch] status={response.status_code} jobs_found={len(items)}")

    # Cap the description length. Job posts run 3000-6000 chars, mostly
    # boilerplate (benefits, EEO statements, company blurb) after the first
    # ~1800 chars of role + requirements. Trimming here cuts LLM token usage
    # across filter/tailor/validate by more than half with no loss of signal.
    MAX_DESC_CHARS = 1800

    jobs = []
    for job in items:
        if not isinstance(job, dict):
            continue
        jobs.append({
            "title":           job.get("job_title", ""),
            "company":         job.get("employer_name", ""),
            "location":        job.get("job_city", location),
            "description":     (job.get("job_description") or "")[:MAX_DESC_CHARS],
            "apply_link":      job.get("job_apply_link", ""),
            "posted_at":       job.get("job_posted_at_datetime_utc", ""),
            "employment_type": job.get("job_employment_type", "")
        })

    return jobs
