from fastapi import APIRouter
from pydantic import BaseModel
from .job_scraper import fetch_live_jobs
from .vector_store import index_jobs, stats
from .matcher import match_resume_to_jobs

router = APIRouter(prefix="/rag", tags=["RAG Matching"])


class MatchRequest(BaseModel):
    resume_text: str
    job_query: str
    location: str = "India"
    num_jobs: int = 50
    top_k: int = 10
    use_cache: bool = True


@router.post("/match-realtime")
def match_realtime(payload: MatchRequest):
    jobs = fetch_live_jobs(
        payload.job_query,
        payload.location,
        payload.num_jobs
    )

    index_jobs(jobs)
    matches = match_resume_to_jobs(payload.resume_text, payload.top_k)

    return {
        "matched_jobs": matches,
        "jobs_fetched": len(jobs),
        "total_matches": len(matches),
        "cache_used": payload.use_cache
    }


@router.get("/stats")
def rag_stats():
    return stats()
