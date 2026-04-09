"""
tools/job_tool.py
==================
Job search tool — wraps the existing job_scraper service so agents can call
fetch_jobs(query) without importing the service directly.

The tool interface is intentionally simple (one function, plain return type)
so it can be registered in an agent's tool registry and called by name.
"""
from __future__ import annotations

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


def fetch_jobs(
    query: str,
    location: str = "India",
    num_jobs: int = 10,
    days_old: int = 14,
) -> List[dict]:
    """
    Fetch live job listings for a query via the existing job_scraper service.

    Args:
        query:    Job title / keyword, e.g. "Software Engineer".
        location: Search location, e.g. "Bangalore".
        num_jobs: Maximum number of results to return.
        days_old: Only return jobs posted within this many days.

    Returns:
        List of job dicts {title, company, location, description, apply_link, ...}
        Returns an empty list on failure (never raises).
    """
    try:
        from backend.services.job_scraper import get_job_scraper
        scraper = get_job_scraper()
        jobs = scraper.fetch_jobs(
            query=query,
            location=location,
            num_jobs=num_jobs,
            days_old=days_old,
        )
        logger.info(f"job_tool.fetch_jobs: retrieved {len(jobs)} jobs for '{query}'")
        return jobs or []
    except Exception as e:
        logger.error(f"job_tool.fetch_jobs failed: {e}")
        return []


def get_job_summary(query: str, location: str = "India", top_n: int = 5) -> str:
    """
    Return a human-readable summary of the top job listings — useful for
    injecting into an LLM prompt as grounded job market context.

    Returns:
        Multi-line string or empty string if no jobs found.
    """
    jobs = fetch_jobs(query, location=location, num_jobs=top_n)
    if not jobs:
        return ""

    lines = [f"Current job listings for '{query}' in {location}:"]
    for i, j in enumerate(jobs, 1):
        lines.append(f"  {i}. {j.get('title','?')} at {j.get('company','?')} ({j.get('location','')})")
    return "\n".join(lines)
