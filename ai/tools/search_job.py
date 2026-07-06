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

    params = {
        "query": f"{job_title} {experience} in {location}",
        "num_pages": "2",
        "date_posted": "month",
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    raw = data.get("data", {})
    items = raw.get("jobs", []) if isinstance(raw, dict) else raw
    print(f"[JSearch] status={response.status_code} jobs_found={len(items)}")

    jobs = []
    for job in items:
        if not isinstance(job, dict):
            continue
        jobs.append({
            "title":           job.get("job_title", ""),
            "company":         job.get("employer_name", ""),
            "location":        job.get("job_city", location),
            "description":     job.get("job_description", ""),
            "apply_link":      job.get("job_apply_link", ""),
            "posted_at":       job.get("job_posted_at_datetime_utc", ""),
            "employment_type": job.get("job_employment_type", "")
        })

    return jobs
