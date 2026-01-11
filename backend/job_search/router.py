"""
Job Search Router - Supports both SERPAPI_KEY and SEARCHAPI_KEY
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import requests
import os
from dotenv import load_dotenv
from pathlib import Path

router = APIRouter()
logger = logging.getLogger(__name__)

# Load .env from backend root
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

# Check for both key names
SERPAPI_KEY = os.getenv("SERPAPI_KEY") or os.getenv("SEARCHAPI_KEY")
if not SERPAPI_KEY:
    logger.warning("⚠️ SERPAPI_KEY/SEARCHAPI_KEY not set in .env file - job search will not work")
else:
    logger.info(f"✅ API Key loaded: {SERPAPI_KEY[:10]}...")


class JobSearchRequest(BaseModel):
    query: str = Field(..., description="Job search keyword")
    location: Optional[str] = Field("Singapore", description="Job location")
    salary_min: Optional[int] = Field(None, description="Minimum salary filter")
    salary_max: Optional[int] = Field(None, description="Maximum salary filter")


@router.post("/", summary="Search jobs using SerpAPI Google Jobs")
async def search_jobs(payload: JobSearchRequest) -> Dict[str, Any]:
    """
    Search for jobs using SerpAPI Google Jobs engine.
    Accepts JSON body with query parameters.
    """
    if not SERPAPI_KEY:
        raise HTTPException(
            status_code=503,
            detail="Job search service not configured. Please add SERPAPI_KEY or SEARCHAPI_KEY to backend/.env file. Get your key from https://serpapi.com/"
        )

    serpapi_url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_jobs",
        "q": payload.query,
        "location": payload.location,
        "api_key": SERPAPI_KEY,
    }

    try:
        logger.info(f"Searching jobs for query='{payload.query}' location='{payload.location}'")
        response = requests.get(serpapi_url, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"SerpAPI request failed: {e}")
        raise HTTPException(
            status_code=502,
            detail="Failed to fetch jobs from external API"
        )

    data = response.json()
    job_results = data.get("jobs_results", [])

    def extract_salary_number(salary_str: str) -> Optional[int]:
        import re
        match = re.search(r'\d+', salary_str.replace(',', ''))
        if match:
            try:
                return int(match.group())
            except ValueError:
                return None
        return None

    filtered_jobs = []
    for job in job_results:
        title = job.get("title", "N/A")
        company = job.get("company_name", "N/A")
        loc = job.get("location", payload.location)
        desc = job.get("description", "No description")
        link = job.get("via", "")
        salary_text = job.get("salary", "Not specified")
        employment_type = job.get("detected_extensions", {}).get("employment_type", "Unknown")

        # Salary filtering
        if (payload.salary_min is not None or payload.salary_max is not None) and salary_text != "Not specified":
            salary_num = extract_salary_number(salary_text)
            if salary_num is not None:
                if payload.salary_min is not None and salary_num < payload.salary_min:
                    continue
                if payload.salary_max is not None and salary_num > payload.salary_max:
                    continue

        filtered_jobs.append({
            "title": title,
            "company": company,
            "location": loc,
            "salary": salary_text,
            "description": desc,
            "via": link,
            "type": employment_type,
        })

    return {
        "jobs": filtered_jobs,
        "total": len(filtered_jobs),
        "source": "SerpAPI",
        "query": payload.query,
        "location": payload.location,
    }


@router.get("/health")
async def health():
    """Health check for job search"""
    return {
        "status": "healthy",
        "service": "job_search",
        "api_configured": bool(SERPAPI_KEY)
    }