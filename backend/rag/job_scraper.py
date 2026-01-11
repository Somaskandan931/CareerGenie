"""
Job Scraper - Fetches jobs from SerpAPI with support for both key names
Save this as: backend/rag/job_scraper.py
"""

import os
import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class JobScraper:
    """Fetches jobs from SerpAPI Google Jobs"""

    def __init__(self):
        # Check for both SERPAPI_KEY and SEARCHAPI_KEY
        self.api_key = os.getenv("SERPAPI_KEY") or os.getenv("SEARCHAPI_KEY")

        if not self.api_key:
            raise ValueError(
                "SERPAPI_KEY or SEARCHAPI_KEY not found in environment. "
                "Please add one of these to your backend/.env file. "
                "Get your key from https://serpapi.com/"
            )

        self.base_url = "https://serpapi.com/search.json"
        logger.info(f"✅ JobScraper initialized with API key: {self.api_key[:10]}...")

    def fetch_jobs(
        self,
        query: str,
        location: str = "India",
        num_results: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Fetch jobs from SerpAPI Google Jobs

        Args:
            query: Job search query (e.g., "software engineer")
            location: Location for job search
            num_results: Number of results to fetch (max ~30-50 per call)

        Returns:
            List of job dictionaries
        """
        try:
            params = {
                "engine": "google_jobs",
                "q": query,
                "location": location,
                "api_key": self.api_key,
                "num": min(num_results, 50)  # SerpAPI limit
            }

            logger.info(f"Fetching jobs: query='{query}', location='{location}'")

            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()
            raw_jobs = data.get("jobs_results", [])

            logger.info(f"Fetched {len(raw_jobs)} jobs from SerpAPI")

            # Transform to standardized format
            jobs = []
            for idx, job in enumerate(raw_jobs):
                try:
                    transformed_job = self._transform_job(job, idx)
                    jobs.append(transformed_job)
                except Exception as e:
                    logger.warning(f"Failed to transform job {idx}: {e}")
                    continue

            logger.info(f"Successfully transformed {len(jobs)} jobs")
            return jobs

        except requests.RequestException as e:
            logger.error(f"SerpAPI request failed: {e}")
            raise Exception(f"Failed to fetch jobs from SerpAPI: {str(e)}")
        except Exception as e:
            logger.error(f"Job fetching error: {e}")
            raise

    def _transform_job(self, raw_job: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Transform SerpAPI job format to our standard format"""

        # Extract job details
        job_id = raw_job.get("job_id") or f"job_{index}_{hash(raw_job.get('title', ''))}"
        title = raw_job.get("title", "Unknown Title")
        company = raw_job.get("company_name", "Unknown Company")
        location = raw_job.get("location", "Unknown Location")
        description = raw_job.get("description", "No description available")

        # Extract extensions (salary, type, etc.)
        extensions = raw_job.get("detected_extensions", {})
        employment_type = extensions.get("employment_type", "Full-time")
        salary_range = extensions.get("salary", "Not specified")

        # Get apply link
        apply_link = raw_job.get("share_link") or raw_job.get("apply_link", "")

        # Extract posted date
        posted_at = raw_job.get("detected_extensions", {}).get("posted_at", "Recently")

        # Extract required skills from description (basic extraction)
        skills = self._extract_skills(description)

        # Extract experience requirement
        experience = self._extract_experience(description)

        return {
            "job_id": job_id,
            "title": title,
            "company": company,
            "location": location,
            "description": description,
            "employment_type": employment_type,
            "salary_range": salary_range,
            "apply_link": apply_link,
            "posted_at": posted_at,
            "skills_required": skills,
            "experience_required": experience,  # Added experience field
            "source": "SerpAPI Google Jobs",
            "fetched_at": datetime.now().isoformat()
        }

    def _extract_skills(self, description: str) -> List[str]:
        """Extract common skills from job description"""
        common_skills = [
            "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
            "React", "Angular", "Vue", "Node.js", "Django", "Flask", "FastAPI",
            "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis",
            "AWS", "Azure", "GCP", "Docker", "Kubernetes",
            "Machine Learning", "Deep Learning", "AI", "Data Science",
            "Git", "CI/CD", "Agile", "Scrum"
        ]

        description_lower = description.lower()
        found_skills = []

        for skill in common_skills:
            if skill.lower() in description_lower:
                found_skills.append(skill)

        return found_skills[:10]  # Limit to top 10

    def _extract_experience(self, description: str) -> str:
        """Extract experience requirement from job description"""
        import re

        description_lower = description.lower()

        # Look for patterns like "5+ years", "3-5 years", "minimum 2 years"
        patterns = [
            r'(\d+)\+?\s*(?:to|\-)\s*(\d+)?\s*years?',
            r'(\d+)\+\s*years?',
            r'minimum\s+(\d+)\s*years?',
            r'at least\s+(\d+)\s*years?',
        ]

        for pattern in patterns:
            match = re.search(pattern, description_lower)
            if match:
                years = match.group(1)
                return f"{years}+ years"

        # Check for entry level or junior
        if 'entry level' in description_lower or 'junior' in description_lower:
            return "0-2 years"

        # Check for senior
        if 'senior' in description_lower:
            return "5+ years"

        return "Not specified"


class JobCache:
    """Simple in-memory cache for job results"""

    def __init__(self, ttl_minutes: int = 60):
        self.cache = {}
        self.ttl = timedelta(minutes=ttl_minutes)
        logger.info(f"JobCache initialized with TTL={ttl_minutes} minutes")

    def _make_key(self, query: str, location: str) -> str:
        """Create cache key"""
        return f"{query.lower().strip()}:{location.lower().strip()}"

    def get(self, query: str, location: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached jobs if not expired"""
        key = self._make_key(query, location)

        if key not in self.cache:
            return None

        cached_data = self.cache[key]
        cached_time = cached_data["timestamp"]

        if datetime.now() - cached_time > self.ttl:
            logger.info(f"Cache expired for key: {key}")
            del self.cache[key]
            return None

        logger.info(f"Cache hit for key: {key}")
        return cached_data["jobs"]

    def set(self, query: str, location: str, jobs: List[Dict[str, Any]]) -> None:
        """Cache jobs"""
        key = self._make_key(query, location)
        self.cache[key] = {
            "jobs": jobs,
            "timestamp": datetime.now()
        }
        logger.info(f"Cached {len(jobs)} jobs for key: {key}")

    def clear(self) -> None:
        """Clear all cache"""
        self.cache.clear()
        logger.info("Cache cleared")


# Singleton instances
_scraper_instance = None
_cache_instance = None


def get_scraper() -> JobScraper:
    """Get singleton scraper instance"""
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = JobScraper()
    return _scraper_instance


def get_cache() -> JobCache:
    """Get singleton cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = JobCache(ttl_minutes=60)
    return _cache_instance