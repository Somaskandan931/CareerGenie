from typing import List, Dict
from serpapi import GoogleSearch
import logging

from backend.config import settings

logger = logging.getLogger(__name__)


class JobScraper:
    def __init__(self):
        if not settings.SERPAPI_KEY:
            raise ValueError("SERPAPI_KEY not configured")

        self.api_key = settings.SERPAPI_KEY

    def fetch_jobs(self, query: str, location: str, num_jobs: int = 50) -> List[Dict]:
        """
        Fetch jobs from Google Jobs via SerpAPI

        Args:
            query: Job search query (e.g., "software engineer")
            location: Location (e.g., "India", "Bangalore")
            num_jobs: Number of jobs to fetch

        Returns:
            List of job dictionaries
        """
        logger.info(f"Fetching jobs: query='{query}', location='{location}', num={num_jobs}")

        params = {
            "engine" : "google_jobs",
            "q" : f"{query} jobs",  # IMPORTANT: improves recall
            "location" : location,  # e.g., Bengaluru, Chennai, Remote
            "gl" : "in",  # Country = India (CRITICAL)
            "hl" : "en",  # Language = English
            "num" : min( num_jobs, 100 ),  # API limit
            "api_key" : self.api_key
        }

        try:
            search = GoogleSearch(params)
            results = search.get_dict()

            jobs_results = results.get("jobs_results", [])
            logger.info(f"Found {len(jobs_results)} jobs")

            jobs = []
            for idx, job in enumerate(jobs_results[:num_jobs]):
                # Safely extract fields first
                title = job.get("title", "Unknown Title")
                company = job.get("company_name", "Unknown Company")

                job_data = {
                    "id": f"job_{idx}_{abs(hash(title + company))}",  # ✅ always valid string
                    "title": title,
                    "company": company,
                    "location": job.get("location", location),
                    "description": job.get("description", ""),
                    "apply_link": self._extract_apply_link(job),
                    "posted_at": job.get("detected_extensions", {}).get("posted_at", ""),
                    "employment_type": job.get("detected_extensions", {}).get("schedule_type", "Full-time"),
                }

                jobs.append(job_data)

            logger.info(f"Successfully processed {len(jobs)} jobs")
            return jobs

        except Exception as e:
            logger.error(f"Error fetching jobs: {str(e)}")
            raise Exception(f"Failed to fetch jobs: {str(e)}")

    def _extract_apply_link(self, job: Dict) -> str:
        """Extract application link from job data"""
        # Try related links first
        related_links = job.get("related_links", [])
        if related_links and isinstance(related_links, list):
            return related_links[0].get("link", "")

        # Fallback to share link
        return job.get("share_link", "")


# Singleton instance
_job_scraper = None


def get_job_scraper():
    global _job_scraper
    if _job_scraper is None:
        _job_scraper = JobScraper()
    return _job_scraper