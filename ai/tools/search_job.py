import re
import requests
import os
from dotenv import load_dotenv

load_dotenv()


def _api_keys() -> list:
    """JSearch RapidAPI keys in try-order: primary, then fallback. The fallback
    covers the primary hitting its daily/monthly quota (429) or being disabled
    (403) — a common failure on RapidAPI free tiers."""
    keys = [os.getenv("JSearch_API"), os.getenv("JSearch_API_FALLBACK")]
    seen, ordered = set(), []
    for k in keys:
        if k and k not in seen:
            seen.add(k)
            ordered.append(k)
    return ordered


def search_jobs(job_title: str, location: str, experience: str) -> list:
    url = "https://jsearch.p.rapidapi.com/search-v2"

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

    # Try each API key in order; fall through to the next on a quota/auth error
    # or a transient failure so a single exhausted key doesn't kill the run.
    keys = _api_keys()
    items = []
    for idx, key in enumerate(keys):
        headers = {"X-RapidAPI-Key": key, "X-RapidAPI-Host": "jsearch.p.rapidapi.com"}
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
        except requests.RequestException as e:
            print(f"[JSearch] key#{idx} request error: {e}")
            continue

        if response.status_code in (401, 403, 429):
            print(f"[JSearch] key#{idx} status={response.status_code} — trying next key")
            continue

        try:
            data = response.json()
        except ValueError:
            print(f"[JSearch] key#{idx} status={response.status_code} — non-JSON body")
            continue

        raw = data.get("data", {})
        items = raw.get("jobs", []) if isinstance(raw, dict) else raw
        print(f"[JSearch] key#{idx} status={response.status_code} jobs_found={len(items)}")
        if response.status_code == 200:
            break  # good response — stop even if 0 jobs (a real empty result)

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
            "location":        _job_location(job, location),
            "description":     (job.get("job_description") or "")[:MAX_DESC_CHARS],
            "apply_link":      job.get("job_apply_link", ""),
            "posted_at":       job.get("job_posted_at_datetime_utc", ""),
            "employment_type": job.get("job_employment_type", "")
        })

    return jobs


def _job_location(job: dict, fallback: str) -> str:
    """Best-effort human location. JSearch often leaves job_city null, so chain
    city -> state -> country, add 'Remote' when flagged, and fall back to the
    searched location so the column is never empty."""
    parts = [job.get("job_city"), job.get("job_state"), job.get("job_country")]
    loc = ", ".join(p for p in parts if p)
    if job.get("job_is_remote"):
        loc = f"Remote{(' · ' + loc) if loc else ''}"
    return loc or fallback or "—"
