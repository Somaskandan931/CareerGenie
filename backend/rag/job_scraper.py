"""
Optimized Job Scraper - Faster fetching with better caching
Save this as: backend/rag/job_scraper.py
"""

import os
import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
import pickle
from pathlib import Path

logger = logging.getLogger(__name__)


class JobScraper:
    """Fetches jobs from SerpAPI Google Jobs with optimizations"""

    def __init__(self):
        self.api_key = os.getenv("SERPAPI_KEY") or os.getenv("SEARCHAPI_KEY")

        if not self.api_key:
            raise ValueError(
                "SERPAPI_KEY or SEARCHAPI_KEY not found in environment. "
                "Please add one of these to your backend/.env file. "
                "Get your key from https://serpapi.com/"
            )

        self.base_url = "https://serpapi.com/search.json"
        # Reduced timeout for faster failures
        self.timeout = 10
        logger.info(f"✅ JobScraper initialized")

    def fetch_jobs(
        self,
        query: str,
        location: str = "India",
        num_results: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Fetch jobs from SerpAPI - optimized version

        Optimizations:
        - Reduced timeout
        - Limit results to 30 max (faster API response)
        - Simplified error handling
        """
        try:
            # Cap at 30 for faster responses
            num_results = min(num_results, 30)

            params = {
                "engine": "google_jobs",
                "q": query,
                "location": location,
                "api_key": self.api_key,
                "num": num_results
            }

            logger.info(f"Fetching {num_results} jobs: '{query}' in '{location}'")

            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            raw_jobs = data.get("jobs_results", [])

            logger.info(f"✅ Fetched {len(raw_jobs)} jobs")

            # Transform jobs - simplified
            jobs = []
            for idx, job in enumerate(raw_jobs):
                try:
                    transformed_job = self._transform_job_fast(job, idx)
                    jobs.append(transformed_job)
                except Exception as e:
                    logger.debug(f"Skipped job {idx}: {e}")
                    continue

            return jobs

        except requests.Timeout:
            logger.error("SerpAPI request timeout")
            return []
        except requests.RequestException as e:
            logger.error(f"SerpAPI request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Job fetching error: {e}")
            return []

    def _transform_job_fast(self, raw_job: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Fast transformation - minimal processing"""

        job_id = raw_job.get("job_id") or f"job_{index}"
        extensions = raw_job.get("detected_extensions", {})

        # Quick skill extraction - only common ones
        description = raw_job.get("description", "")
        skills = self._extract_skills_fast(description)

        return {
            "job_id": job_id,
            "title": raw_job.get("title", "Unknown"),
            "company": raw_job.get("company_name", "Unknown"),
            "location": raw_job.get("location", "Unknown"),
            "description": description[:500],  # Truncate for speed
            "employment_type": extensions.get("employment_type", "Full-time"),
            "salary_range": extensions.get("salary", "Not specified"),
            "apply_link": raw_job.get("share_link") or raw_job.get("apply_link", ""),
            "posted_at": extensions.get("posted_at", "Recently"),
            "skills_required": skills,
            "experience_required": self._extract_experience_fast(description),
            "source": "SerpAPI",
            "fetched_at": datetime.now().isoformat()
        }

    def _extract_skills_fast(self, description: str) -> List[str]:
        """Fast skill extraction - limited set"""
        # Reduced skill list for faster matching
        priority_skills = [
            "Python", "Java", "JavaScript", "React", "Node.js",
            "SQL", "AWS", "Docker", "Machine Learning", "AI"
        ]

        description_lower = description.lower()
        found = []

        for skill in priority_skills:
            if skill.lower() in description_lower:
                found.append(skill)
                if len(found) >= 5:  # Max 5 skills for speed
                    break

        return found

    def _extract_experience_fast(self, description: str) -> str:
        """Fast experience extraction"""
        description_lower = description.lower()

        # Quick checks only
        if 'entry level' in description_lower or 'junior' in description_lower:
            return "0-2 years"
        if 'senior' in description_lower:
            return "5+ years"

        return "Not specified"


class JobCache:
    """Persistent disk-based cache for better performance"""

    def __init__(self, ttl_hours: int = 24, cache_dir: str = "./cache"):
        self.ttl = timedelta(hours=ttl_hours)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        logger.info(f"JobCache initialized with TTL={ttl_hours} hours")

    def _make_key(self, query: str, location: str) -> str:
        """Create hash-based cache key"""
        key_str = f"{query.lower().strip()}:{location.lower().strip()}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path"""
        return self.cache_dir / f"{key}.pkl"

    def get(self, query: str, location: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached jobs from disk"""
        key = self._make_key(query, location)
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'rb') as f:
                cached_data = pickle.load(f)

            cached_time = cached_data["timestamp"]

            if datetime.now() - cached_time > self.ttl:
                logger.info(f"Cache expired for key: {key}")
                cache_path.unlink()
                return None

            logger.info(f"✅ Cache hit: {len(cached_data['jobs'])} jobs")
            return cached_data["jobs"]

        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            return None

    def set(self, query: str, location: str, jobs: List[Dict[str, Any]]) -> None:
        """Cache jobs to disk"""
        key = self._make_key(query, location)
        cache_path = self._get_cache_path(key)

        try:
            cached_data = {
                "jobs": jobs,
                "timestamp": datetime.now()
            }

            with open(cache_path, 'wb') as f:
                pickle.dump(cached_data, f)

            logger.info(f"✅ Cached {len(jobs)} jobs")

        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    def clear(self) -> None:
        """Clear all cache files"""
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()
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
        _cache_instance = JobCache(ttl_hours=24)
    return _cache_instance