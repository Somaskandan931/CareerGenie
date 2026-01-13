import os
from typing import List, Dict
from serpapi import GoogleSearch


def fetch_live_jobs(query: str, location: str, num_jobs: int) -> List[Dict]:
    serpapi_key = os.getenv("SERPAPI_KEY")

    if not serpapi_key:
        raise RuntimeError(
            "SERPAPI_KEY is not set. Ensure .env is loaded before starting the server."
        )

    params = {
        "engine": "google_jobs",
        "q": query,
        "location": location,
        "api_key": serpapi_key
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    jobs = []

    for job in results.get("jobs_results", [])[:num_jobs]:
        jobs.append({
            "title": job.get("title"),
            "company": job.get("company_name"),
            "location": job.get("location"),
            "description": job.get("description", ""),
            "apply_link": (
                job.get("related_links", [{}])[0].get("link", "")
                if job.get("related_links")
                else ""
            )
        })

    return jobs
