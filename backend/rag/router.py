"""
RAG Router - Complete version with comprehensive error handling
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import os

try:
    from backend.rag.vector_store import get_vector_store
    from backend.rag.matcher import RAGJobMatcher
    from backend.rag.job_scraper import get_scraper, get_cache
except ImportError:
    from rag.vector_store import get_vector_store
    from rag.matcher import RAGJobMatcher
    from rag.job_scraper import get_scraper, get_cache

router = APIRouter()
logger = logging.getLogger(__name__)

matcher = RAGJobMatcher()


class RAGMatchRequest(BaseModel):
    """Request for RAG matching from vector store"""
    resume_text: str = Field(..., description="Full resume text")
    top_k: Optional[int] = Field(10, description="Number of jobs to retrieve", ge=1, le=50)


class RealTimeRAGRequest(BaseModel):
    """Request for real-time RAG matching"""
    resume_text: str = Field(..., min_length=10, description="Full resume text")
    job_query: str = Field(..., min_length=1, description="Job search query")
    location: Optional[str] = Field("India", description="Job location")
    num_jobs: Optional[int] = Field(30, description="Jobs to fetch", ge=5, le=50)
    top_k: Optional[int] = Field(10, description="Top matches to return", ge=1, le=20)
    use_cache: Optional[bool] = Field(True, description="Use cached jobs")


class RAGMatchResponse(BaseModel):
    """Response with matched jobs"""
    matched_jobs: List[Dict[str, Any]]
    total_matches: int
    retrieval_method: str = "RAG (Retrieval-Augmented Generation)"
    vector_store_stats: Dict[str, Any]


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
    summary="Real-time RAG job matching",
    description="Fetch live jobs, index them, and generate explainable matches"
)
async def match_jobs_realtime(request: RealTimeRAGRequest) -> RealTimeRAGResponse:
    """
    Complete RAG pipeline:
    1. Fetch live jobs from SearchAPI
    2. Auto-index to vector store
    3. Semantic search
    4. Generate explainable matches with LLM
    """
    warnings = []
    error_message = None

    try:
        logger.info(f"=== RAG Request Started ===")
        logger.info(f"Query: '{request.job_query}', Location: '{request.location}'")

        # Validate inputs
        job_query = request.job_query.strip()
        location = (request.location or "India").strip()

        if not job_query:
            raise HTTPException(status_code=400, detail="Job query cannot be empty")

        if len(job_query) > 100:
            job_query = job_query[:100]
            warnings.append("Query truncated to 100 characters")

        num_jobs = min(max(5, request.num_jobs), 50)
        top_k = min(max(1, request.top_k), 20)

        # Get component instances with better error messages
        try:
            scraper = get_scraper()
            cache = get_cache()
            vector_store = get_vector_store()
        except Exception as e:
            error_str = str(e)
            logger.error(f"Failed to initialize components: {error_str}")

            # Check if it's an API key issue
            if "SEARCHAPI_KEY" in error_str or "SERPAPI_KEY" in error_str:
                raise HTTPException(
                    status_code=503,
                    detail="Job search service not configured. Please add SEARCHAPI_KEY or SERPAPI_KEY to your backend/.env file. Get your key from https://serpapi.com/"
                )
            elif "ANTHROPIC_API_KEY" in error_str:
                raise HTTPException(
                    status_code=503,
                    detail="AI matching service not configured. Please add ANTHROPIC_API_KEY to your backend/.env file. Get your key from https://console.anthropic.com/"
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"System initialization failed: {error_str}. Please check your backend configuration."
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
                logger.info(f"Using {len(jobs)} cached jobs")
            else:
                logger.info("Cache miss - fetching fresh jobs")
                jobs = await _fetch_jobs(scraper, job_query, location, num_jobs)

                if jobs:
                    cache.set(job_query, location, jobs)
                else:
                    error_message = (
                        f"No jobs found for '{job_query}' in '{location}'. "
                        "Try a simpler search term or different location."
                    )
        else:
            logger.info("Cache disabled - fetching fresh jobs")
            jobs = await _fetch_jobs(scraper, job_query, location, num_jobs)

            if not jobs:
                error_message = (
                    f"No jobs found for '{job_query}' in '{location}'. "
                    "Try a simpler search term or different location."
                )

        logger.info(f"Total jobs available: {len(jobs)}")

        # Return early if no jobs
        if not jobs:
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

        # Index jobs to vector store
        try:
            vector_store.add_jobs(jobs)
            logger.info(f"Indexed {len(jobs)} jobs")
        except Exception as e:
            logger.error(f"Indexing failed: {e}")
            warnings.append("Job indexing had issues - using fallback matching")

        # Retrieve semantically similar jobs
        try:
            retrieved_jobs = vector_store.search_jobs(
                resume_text=request.resume_text,
                top_k=min(top_k, len(jobs))
            )
            logger.info(f"Retrieved {len(retrieved_jobs)} similar jobs")
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            retrieved_jobs = jobs[:top_k]
            warnings.append("Semantic search unavailable - using recent jobs")

        # Generate explainable matches
        try:
            matched_jobs = matcher.match_jobs(request.resume_text, retrieved_jobs)
            logger.info(f"Generated {len(matched_jobs)} matches")
        except Exception as e:
            logger.error(f"Match generation failed: {e}")
            warnings.append("Advanced matching unavailable - using basic scoring")

            # Fallback matching
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
        logger.exception("Real-time RAG matching failed")
        raise HTTPException(
            status_code=500,
            detail=f"Matching failed: {str(e)}"
        )


async def _fetch_jobs(
        scraper,
        query: str,
        location: str,
        num_jobs: int
) -> List[Dict[str, Any]]:
    """Fetch jobs with error handling"""
    try:
        jobs = scraper.fetch_jobs(
            query=query,
            location=location,
            num_results=num_jobs
        )
        return jobs
    except Exception as e:
        logger.error(f"Job fetching failed: {e}")
        return []


def _fallback_matching(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Fallback matching when main matcher fails"""
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
            "explanation": "Match scoring temporarily unavailable",
            "recommendation": "Review job details to determine fit"
        }
        for job in jobs
    ]


@router.post(
    "/match",
    response_model=RAGMatchResponse,
    summary="Match resume to jobs in vector store",
    description="Use existing vector store for matching"
)
async def match_jobs_rag(request: RAGMatchRequest) -> RAGMatchResponse:
    """Match resume to jobs already in vector store"""
    try:
        vector_store = get_vector_store()

        retrieved_jobs = vector_store.search_jobs(
            resume_text=request.resume_text,
            top_k=request.top_k
        )

        if not retrieved_jobs:
            return RAGMatchResponse(
                matched_jobs=[],
                total_matches=0,
                vector_store_stats=vector_store.get_stats()
            )

        matched_jobs = matcher.match_jobs(request.resume_text, retrieved_jobs)

        return RAGMatchResponse(
            matched_jobs=matched_jobs,
            total_matches=len(matched_jobs),
            vector_store_stats=vector_store.get_stats()
        )

    except Exception as e:
        logger.exception("RAG matching failed")
        raise HTTPException(
            status_code=500,
            detail=f"Matching failed: {str(e)}"
        )


@router.post("/admin/load-jobs", summary="Load jobs from JSON file")
async def load_jobs(json_path: str = "data/jobs/sample_jobs.json") -> Dict[str, Any]:
    """Admin endpoint to load jobs from file"""
    try:
        vector_store = get_vector_store()
        count = vector_store.load_jobs_from_file(json_path)

        return {
            "message": f"Loaded {count} jobs",
            "stats": vector_store.get_stats()
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {json_path}")
    except Exception as e:
        logger.exception("Failed to load jobs")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", summary="Get vector store statistics")
async def get_stats() -> Dict[str, Any]:
    """Get vector store stats"""
    try:
        vector_store = get_vector_store()
        return vector_store.get_stats()
    except Exception as e:
        logger.exception("Failed to get stats")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/admin/clear", summary="Clear vector store")
async def clear_vector_store() -> Dict[str, str]:
    """Clear all jobs from vector store"""
    try:
        vector_store = get_vector_store()
        vector_store.clear_all()
        return {"message": "Vector store cleared"}
    except Exception as e:
        logger.exception("Failed to clear store")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", summary="RAG system health check")
async def health_check() -> Dict[str, Any]:
    """Check RAG system health"""
    health = {
        "status": "healthy",
        "components": {}
    }

    # Check if API keys are configured
    searchapi_key = os.getenv("SEARCHAPI_KEY") or os.getenv("SERPAPI_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if not searchapi_key:
        health["components"]["searchapi_key"] = "missing - add to backend/.env"
        health["status"] = "degraded"
    else:
        health["components"]["searchapi_key"] = "configured"

    if not anthropic_key:
        health["components"]["anthropic_key"] = "missing - add to backend/.env"
        health["status"] = "degraded"
    else:
        health["components"]["anthropic_key"] = "configured"

    try:
        scraper = get_scraper()
        health["components"]["scraper"] = "ok"
    except Exception as e:
        health["components"]["scraper"] = f"error: {str(e)}"
        health["status"] = "degraded"

    try:
        vector_store = get_vector_store()
        stats = vector_store.get_stats()
        health["components"]["vector_store"] = f"ok ({stats['total_jobs']} jobs)"
    except Exception as e:
        health["components"]["vector_store"] = f"error: {str(e)}"
        health["status"] = "degraded"

    try:
        cache = get_cache()
        health["components"]["cache"] = "ok"
    except Exception as e:
        health["components"]["cache"] = f"error: {str(e)}"
        health["status"] = "degraded"

    try:
        health["components"]["matcher"] = "ok"
    except Exception as e:
        health["components"]["matcher"] = f"error: {str(e)}"
        health["status"] = "degraded"

    return health