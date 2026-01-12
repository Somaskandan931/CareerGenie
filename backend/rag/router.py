"""
Optimized RAG Router - Faster job matching
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import os
import asyncio

try:
    from backend.rag.vector_store import get_vector_store
    from backend.rag.matcher import RAGJobMatcher
    from backend.rag.job_scraper import get_scraper, get_cache
except ImportError:
    from backend.rag.vector_store import get_vector_store
    from backend.rag.matcher import RAGJobMatcher
    from backend.rag.job_scraper import get_scraper, get_cache

router = APIRouter()
logger = logging.getLogger(__name__)

matcher = RAGJobMatcher()


class RealTimeRAGRequest(BaseModel):
    """Request for real-time RAG matching"""
    resume_text: str = Field(..., min_length=10, description="Full resume text")
    job_query: str = Field(..., min_length=1, description="Job search query")
    location: Optional[str] = Field("India", description="Job location")
    num_jobs: Optional[int] = Field(20, description="Jobs to fetch", ge=5, le=30)
    top_k: Optional[int] = Field(10, description="Top matches to return", ge=1, le=10)
    use_cache: Optional[bool] = Field(True, description="Use cached jobs")


class RealTimeRAGResponse(BaseModel):
    """Response for real-time RAG"""
    matched_jobs: List[Dict[str, Any]]
    jobs_fetched: int
    total_matches: int
    retrieval_method: str = "Real-Time RAG"
    cache_used: bool
    query: str
    location: str
    error_message: Optional[str] = None
    warnings: List[str] = []


@router.post(
    "/match-realtime",
    response_model=RealTimeRAGResponse,
    summary="Optimized real-time RAG job matching",
    description="Faster job fetching and matching pipeline"
)
async def match_jobs_realtime(request: RealTimeRAGRequest) -> RealTimeRAGResponse:
    """
    Optimized RAG pipeline:
    1. Check cache first (instant)
    2. Fetch only if needed (parallel)
    3. Quick indexing (batch)
    4. Fast matching (top 10 only)

    Expected time: 2-5 seconds (cached) or 5-10 seconds (fresh)
    """
    warnings = []
    error_message = None

    try:
        logger.info(f"🚀 RAG Request: '{request.job_query}' in '{request.location}'")

        # Validate and sanitize inputs
        job_query = request.job_query.strip()
        location = (request.location or "India").strip()

        if not job_query:
            raise HTTPException(status_code=400, detail="Job query cannot be empty")

        # Cap limits for speed
        num_jobs = min(max(5, request.num_jobs), 20)  # Max 20 jobs
        top_k = min(max(1, request.top_k), 10)  # Max 10 matches

        # Initialize components
        try:
            scraper = get_scraper()
            cache = get_cache()
            vector_store = get_vector_store()
        except Exception as e:
            logger.error(f"Component initialization failed: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Service initialization failed: {str(e)}"
            )

        # Fetch or get cached jobs
        cache_used = False
        jobs = []

        if request.use_cache:
            logger.info("Checking cache...")
            cached_jobs = cache.get(job_query, location)

            if cached_jobs:
                jobs = cached_jobs
                cache_used = True
                logger.info(f"✅ Cache hit: {len(jobs)} jobs")
            else:
                logger.info("Cache miss - fetching...")
                jobs = await _fetch_jobs_async(scraper, job_query, location, num_jobs)
                if jobs:
                    cache.set(job_query, location, jobs)
        else:
            jobs = await _fetch_jobs_async(scraper, job_query, location, num_jobs)

        if not jobs:
            error_message = f"No jobs found for '{job_query}' in '{location}'"
            return RealTimeRAGResponse(
                matched_jobs=[],
                jobs_fetched=0,
                total_matches=0,
                cache_used=cache_used,
                query=job_query,
                location=location,
                error_message=error_message,
                warnings=warnings
            )

        logger.info(f"📊 Processing {len(jobs)} jobs")

        # Index jobs (batch operation - fast)
        try:
            vector_store.add_jobs(jobs)
        except Exception as e:
            logger.warning(f"Indexing issue: {e}")
            warnings.append("Using fallback matching")

        # Semantic search
        try:
            retrieved_jobs = vector_store.search_jobs(
                resume_text=request.resume_text,
                top_k=min(top_k, len(jobs))
            )
            logger.info(f"🔍 Retrieved {len(retrieved_jobs)} similar jobs")
        except Exception as e:
            logger.error(f"Search failed: {e}")
            retrieved_jobs = jobs[:top_k]
            warnings.append("Using basic matching")

        # Generate matches (fast for top jobs only)
        try:
            matched_jobs = matcher.match_jobs(request.resume_text, retrieved_jobs)
            logger.info(f"✅ Matched {len(matched_jobs)} jobs")
        except Exception as e:
            logger.error(f"Matching failed: {e}")
            warnings.append("Using simplified scoring")
            matched_jobs = _fallback_matching(retrieved_jobs)

        return RealTimeRAGResponse(
            matched_jobs=matched_jobs,
            jobs_fetched=len(jobs),
            total_matches=len(matched_jobs),
            cache_used=cache_used,
            query=job_query,
            location=location,
            error_message=error_message,
            warnings=warnings
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("RAG matching failed")
        raise HTTPException(
            status_code=500,
            detail=f"Matching failed: {str(e)}"
        )


async def _fetch_jobs_async(
    scraper,
    query: str,
    location: str,
    num_jobs: int
) -> List[Dict[str, Any]]:
    """Async wrapper for job fetching"""
    try:
        # Run in thread pool to not block
        loop = asyncio.get_event_loop()
        jobs = await loop.run_in_executor(
            None,
            scraper.fetch_jobs,
            query,
            location,
            num_jobs
        )
        return jobs
    except Exception as e:
        logger.error(f"Job fetching failed: {e}")
        return []


def _fallback_matching(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Simple fallback matching"""
    return [
        {
            "job_id": job["job_id"],
            "title": job["title"],
            "company": job["company"],
            "location": job["location"],
            "employment_type": job.get("employment_type", "Full-time"),
            "salary_range": job.get("salary_range", "Not specified"),
            "apply_link": job["apply_link"],
            "match_score": 50.0,
            "skill_match_score": 50.0,
            "semantic_match_score": 50.0,
            "matched_skills": [],
            "missing_required_skills": [],
            "missing_preferred_skills": [],
            "explanation": "Basic match - detailed scoring unavailable",
            "recommendation": "Review details to determine fit"
        }
        for job in jobs[:10]  # Top 10 only
    ]


@router.get("/health", summary="RAG system health check")
async def health_check() -> Dict[str, Any]:
    """Check RAG system health"""
    health = {
        "status": "healthy",
        "components": {}
    }

    searchapi_key = os.getenv("SEARCHAPI_KEY") or os.getenv("SERPAPI_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    health["components"]["searchapi_key"] = "configured" if searchapi_key else "missing"
    health["components"]["anthropic_key"] = "configured" if anthropic_key else "missing"

    if not searchapi_key or not anthropic_key:
        health["status"] = "degraded"

    try:
        vector_store = get_vector_store()
        stats = vector_store.get_stats()
        health["components"]["vector_store"] = f"ok ({stats['total_jobs']} jobs)"
    except Exception as e:
        health["components"]["vector_store"] = f"error: {str(e)}"
        health["status"] = "degraded"

    return health


@router.get("/stats", summary="Get vector store statistics")
async def get_stats() -> Dict[str, Any]:
    """Get vector store stats"""
    try:
        vector_store = get_vector_store()
        return vector_store.get_stats()
    except Exception as e:
        logger.exception("Failed to get stats")
        raise HTTPException(status_code=500, detail=str(e))