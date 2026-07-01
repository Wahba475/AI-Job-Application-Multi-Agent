import requests
import os
from dotenv import load_dotenv

load_dotenv()

def search_jobs(job_title: str, location: str, experience: str, num_results: int = 5) -> list:
    """
    Search for jobs using the JSearch API.
    Args:
        job_title (str): The job title to search for.
        location (str): The location to search for.
        experience (str): The experience level to search for.
        num_results (int): The number of results to return.
    Returns:
        list: A list of jobs.
    """
    
    url = "https://jsearch.p.rapidapi.com/search"
    
    headers = {
        "X-RapidAPI-Key": os.getenv("JSearch_API"),
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    
    params = {
        "query": f"{experience} {job_title} in {location}",
        "num_pages": "1",
        "country": "eg",
        "date_posted": "week",
        "employment_types": "FULLTIME,INTERN",
        "fields": "job_title,employer_name,job_city,job_description,job_apply_link,job_posted_at_datetime_utc,job_employment_type"
    }
    
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    
    jobs = []
    for job in data.get("data", []):
        jobs.append({
            "title": job.get("job_title", ""),
            "company": job.get("employer_name", ""),
            "location": job.get("job_city", location),
            "description": job.get("job_description", ""),
            "apply_link": job.get("job_apply_link", ""),
            "posted_at": job.get("job_posted_at_datetime_utc", ""),
            "employment_type": job.get("job_employment_type", "")
        })
    
    return jobs