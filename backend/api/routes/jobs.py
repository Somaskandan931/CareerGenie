"""
Jobs API Routes
===============
Endpoints for job search, matching, and posting.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.core.logging import get_logger
from backend.services.vector_store import vector_store
from backend.services.matcher import get_job_matcher
from backend.services.job_scraper import get_job_scraper
from backend.services.career_advisor import career_advisor
from backend.services.enhanced_skill_extractor import EnhancedSkillExtractor

logger = get_logger("routes.jobs")

router = APIRouter(prefix="/jobs", tags=["Jobs"])


# ── Helper ─────────────────────────────────────────────────────────────────────

def _require_vector_store():
    """Raise 503 if vector store failed to initialise."""
    if vector_store is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Vector store unavailable. "
                "Check server logs for initialisation errors. "
                "Try POST /jobs/admin/reset-vector-store to recover."
            ),
        )
    return vector_store


# ── Request/Response Models ─────────────────────────────────────────────────────

class JobMatchRequest(BaseModel):
    resume_text: str
    job_query: str
    location: str = "India"
    num_jobs: int = Field(default=50, ge=1, le=100)
    top_k: int = Field(default=10, ge=1, le=50)
    user_id: Optional[str] = None
    min_match_score: float = Field(default=40.0, ge=0, le=100)
    experience_level: Optional[str] = None
    posted_within_days: Optional[int] = 14
    exclude_remote: bool = False
    force_refresh: bool = False


class JobMatch(BaseModel):
    job_id: str
    title: str
    company: str
    location: str
    match_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    explanation: str
    recommendation: str
    apply_link: Optional[str] = None
    semantic_score: Optional[float] = None
    skills_score: Optional[float] = None
    title_score: Optional[float] = None
    ltr_score: Optional[float] = None
    ltr_rank: Optional[int] = None
    personalised: Optional[bool] = False


class JobMatchResponse(BaseModel):
    matched_jobs: List[JobMatch]
    total_jobs_fetched: int
    total_jobs_indexed: int
    search_query: str
    career_advice: Optional[Dict] = None
    skill_comparison: Optional[Dict] = None


class JobPostRequest(BaseModel):
    title: str
    company: str
    location: str = "India"
    description: str
    requirements: Optional[str] = None
    employment_type: str = "Full-time"
    salary_range: Optional[str] = None
    contact_email: Optional[str] = None
    posted_by: Optional[str] = None


class JobPostResponse(BaseModel):
    status: str
    job_id: str
    indexed: int
    message: str


class VectorStoreStatus(BaseModel):
    total_jobs: int
    freshness: str
    embedder: str
    sample_jobs: List[Dict]
    collection_exists: bool


# ── Routes ──────────────────────────────────────────────────────────────────────

@router.post("/match", response_model=JobMatchResponse)
async def match_jobs(request: JobMatchRequest):
    """Match resume to jobs in real-time using RAG."""
    vs = _require_vector_store()

    try:
        matcher = get_job_matcher()

        stats_before = vs.get_stats()
        if stats_before["total_jobs"] < 10 or request.force_refresh:
            await _refresh_jobs(
                request.resume_text,
                request.location,
                job_query=request.job_query,
                num_jobs=request.num_jobs,
            )

        stats_after = vs.get_stats()

        matches = matcher.match_resume_to_jobs(
            request.resume_text,
            top_k=request.top_k,
            location=request.location,
            user_id=request.user_id,
            force_refresh=request.force_refresh,
        )

        matches = [m for m in matches if m.get("match_score", 0) >= request.min_match_score]

        advice = career_advisor.generate_career_advice(
            resume_text=request.resume_text,
            target_role=matcher._extract_target_role(request.resume_text),
            job_matches=matches,
        )

        extractor = EnhancedSkillExtractor()
        resume_skills = extractor.extract_skills_with_context(request.resume_text)
        skill_comparison = {"resume_skills": resume_skills, "job_skills": []}

        return JobMatchResponse(
            matched_jobs=matches,
            total_jobs_fetched=stats_after.get("total_jobs", len(matches)),
            total_jobs_indexed=stats_after.get("total_jobs", len(matches)),
            search_query=request.job_query or "",
            career_advice=advice,
            skill_comparison=skill_comparison,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Job match error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/post", response_model=JobPostResponse)
async def post_job(request: JobPostRequest):
    """Allow employers to post a job directly into the vector store."""
    vs = _require_vector_store()

    try:
        import uuid
        from datetime import datetime

        job = {
            "id": f"posted_{uuid.uuid4().hex[:8]}",
            "title": request.title,
            "company": request.company,
            "location": request.location,
            "description": f"{request.description}\n\nRequirements: {request.requirements or ''}",
            "employment_type": request.employment_type,
            "salary_range": request.salary_range or "Not disclosed",
            "apply_link": f"mailto:{request.contact_email}" if request.contact_email else None,
            "posted_at": "Just now",
            "days_old": 0,
            "fetched_at": datetime.now().isoformat(),
            "source": "employer_posted",
            "posted_by": request.posted_by or "",
        }

        indexed = vs.index_jobs([job])
        return JobPostResponse(
            status="success",
            job_id=job["id"],
            indexed=indexed,
            message=f"Job '{request.title}' at {request.company} is now live.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Job post error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/posted")
async def list_posted_jobs():
    """List all employer-posted jobs."""
    vs = _require_vector_store()

    try:
        # FIX: use ChromaDB 'where' filter instead of post-hoc Python filter
        # so we don't miss jobs that didn't surface in a semantic search.
        try:
            result = vs.collection.get(
                where={"source": "employer_posted"},
                include=["metadatas", "documents"],
            )
            jobs = []
            for idx, meta in enumerate(result.get("metadatas") or []):
                jobs.append({
                    "id": result["ids"][idx],
                    "title": meta.get("title", ""),
                    "company": meta.get("company", ""),
                    "location": meta.get("location", ""),
                    "description": (result.get("documents") or [""])[idx],
                    "apply_link": meta.get("apply_link", ""),
                    "posted_at": meta.get("posted_at", ""),
                    "source": "employer_posted",
                })
            return {"jobs": jobs, "total": len(jobs)}
        except Exception:
            # Fallback for older Chroma versions that don't support 'where' on get()
            jobs = vs.search("job position employer posted", top_k=200)
            posted = [j for j in jobs if j.get("source") == "employer_posted"]
            return {"jobs": posted, "total": len(posted)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List posted jobs error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vector-store/status", response_model=VectorStoreStatus)
async def vector_store_status():
    """Get vector store statistics and health."""
    if vector_store is None:
        return VectorStoreStatus(
            total_jobs=0, freshness="unavailable", embedder="unavailable",
            sample_jobs=[], collection_exists=False,
        )

    try:
        stats = vector_store.get_stats()
        sample = []
        if stats["total_jobs"] > 0:
            try:
                sample_jobs = vector_store.search("software", top_k=3)
                sample = [
                    {"title": j.get("title", ""), "company": j.get("company", ""), "location": j.get("location", "")}
                    for j in sample_jobs
                ]
            except Exception as e:
                sample = [{"error": str(e)}]

        return VectorStoreStatus(
            total_jobs=stats["total_jobs"],
            freshness=stats.get("freshness", "unknown"),
            embedder=stats.get("embedder", "unknown"),
            sample_jobs=sample,
            collection_exists=True,
        )
    except Exception as e:
        logger.error(f"Status error: {e}", exc_info=True)
        return VectorStoreStatus(
            total_jobs=0, freshness="unknown", embedder="unknown",
            sample_jobs=[], collection_exists=False,
        )


@router.post("/admin/refresh")
async def admin_refresh_jobs(resume_text: str = "", location: str = "India"):
    """Manually refresh jobs in vector store."""
    vs = _require_vector_store()

    try:
        matcher = get_job_matcher()
        target_role = matcher._extract_target_role(resume_text) if resume_text else "Software Engineer"

        scraper = get_job_scraper()
        jobs = scraper.fetch_jobs(query=target_role, location=location, num_jobs=50)

        if jobs:
            indexed = vs.index_jobs(jobs)
            return {
                "status": "success",
                "jobs_fetched": len(jobs),
                "jobs_indexed": indexed,
                "target_role": target_role,
                "total_jobs": vs.get_stats()["total_jobs"],
            }
        return {"status": "error", "message": "No jobs found"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refresh jobs error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/force-refresh")
async def admin_force_refresh_jobs(
    query: str = "Software Engineer",
    location: str = "India",
    num_jobs: int = 30,
):
    """Force refresh all jobs in vector store."""
    vs = _require_vector_store()

    try:
        vs.clear()
        scraper = get_job_scraper()
        jobs = scraper.fetch_jobs(query=query, location=location, num_jobs=num_jobs, days_old=30)

        if not jobs:
            return {"status": "error", "message": f"No jobs found for '{query}' in {location}", "jobs_fetched": 0}

        indexed = vs.index_jobs(jobs)
        return {
            "status": "success",
            "query": query,
            "location": location,
            "jobs_fetched": len(jobs),
            "jobs_indexed": indexed,
            "total_jobs_in_store": vs.get_stats()["total_jobs"],
            "sample_job": jobs[0] if jobs else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Force refresh error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/seed-mock")
async def admin_seed_mock_jobs(
    query: str = "Software Engineer",
    location: str = "India",
    num_jobs: int = 20,
):
    """Seed vector store with mock jobs for testing."""
    vs = _require_vector_store()

    try:
        from datetime import datetime

        vs.clear()
        roles = [
            f"Senior {query}", f"Junior {query}", f"Lead {query}",
            f"{query} Specialist", f"{query} Developer", f"Principal {query}",
            f"{query} Architect", f"{query} Consultant", f"Staff {query}",
        ]
        companies = ["Google", "Microsoft", "Amazon", "Apple", "Meta", "Netflix", "Tesla"]

        mock_jobs = [
            {
                "id": f"seed_job_{i}",
                "title": roles[i % len(roles)],
                "company": companies[i % len(companies)],
                "location": location,
                "description": (
                    f"We are hiring a {roles[i % len(roles)]} at {companies[i % len(companies)]}. "
                    f"Requirements: Experience in {query}, strong coding skills, team player."
                ),
                "apply_link": f"https://example.com/jobs/seed_job_{i}",
                "posted_at": f"{i + 1} days ago",
                "employment_type": "Full-time",
                "days_old": i,
                "fetched_at": datetime.now().isoformat(),
            }
            for i in range(num_jobs)
        ]

        indexed = vs.index_jobs(mock_jobs)
        return {
            "status": "success",
            "jobs_created": len(mock_jobs),
            "jobs_indexed": indexed,
            "total_jobs": vs.get_stats()["total_jobs"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Seed error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/reset-vector-store")
async def admin_reset_vector_store():
    """Reset vector store to fix dimension mismatch."""
    try:
        import shutil
        from pathlib import Path
        from backend.core.config import settings

        chroma_dir = Path(settings.CHROMA_PERSIST_DIR)
        if chroma_dir.exists():
            shutil.rmtree(chroma_dir)
            logger.info(f"Deleted {chroma_dir}")
            chroma_dir.mkdir(parents=True, exist_ok=True)

        if vector_store is not None:
            vector_store.clear()

        return {
            "status": "success",
            "message": "Vector store reset. The next match request will re-index jobs.",
            "directory": str(chroma_dir),
        }
    except Exception as e:
        logger.error(f"Reset error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── Helper Functions ────────────────────────────────────────────────────────────

async def _refresh_jobs(
    resume_text: str,
    location: str,
    job_query: str = None,
    num_jobs: int = 50,
):
    """Refresh job index in background."""
    vs = vector_store
    if vs is None:
        return
    try:
        matcher = get_job_matcher()
        target_role = job_query.strip() if job_query else matcher._extract_target_role(resume_text)

        scraper = get_job_scraper()
        jobs = scraper.fetch_jobs(query=target_role, location=location, num_jobs=num_jobs)

        if jobs:
            vs.index_jobs(jobs)
            logger.info(f"Refreshed {len(jobs)} jobs for query='{target_role}'")
    except Exception as e:
        logger.error(f"Job refresh failed: {e}")
