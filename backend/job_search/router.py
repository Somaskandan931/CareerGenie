from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import requests
import os

router = APIRouter()

# ✅ Load .env variables
load_dotenv()
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

@router.get("/search-jobs")
def search_jobs(query: str = Query(...), location: str = Query("India")):
    try:
        url = "https://serpapi.com/search"
        params = {
            "engine": "google_jobs",
            "q": f"{query} jobs in {location}",
            "api_key": SERPAPI_KEY
        }

        response = requests.get(url, params=params)

        if response.status_code != 200:
            return JSONResponse(status_code=response.status_code, content={"error": "Failed to fetch jobs"})

        jobs_data = response.json().get("jobs_results", [])[:10]
        results = [
            {
                "title": job.get("title"),
                "company": job.get("company_name"),
                "location": job.get("location"),
                "description": job.get("description"),
                "url": job.get("via")  # this is typically "Google", etc.
            }
            for job in jobs_data
        ]

        return {"results": results}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
