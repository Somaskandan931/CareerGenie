"""
Mentor API Routes
=================
Endpoints for mentor search and session booking.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.core.logging import get_logger

logger = get_logger("routes.mentor")

router = APIRouter(prefix="/mentor", tags=["Mentor"])


class MentorSearchBody(BaseModel):
    query: Optional[str] = None
    domain: Optional[str] = None
    user_skills: Optional[List[str]] = None
    user_id: Optional[str] = None
    expertise: Optional[List[str]] = None
    industry: Optional[str] = None
    language: Optional[str] = None
    max_rate: Optional[float] = None
    min_rating: float = 4.0
    country: Optional[str] = None


class MentorBookBody(BaseModel):
    mentor_id: str
    user_id: str
    date: Optional[str] = None
    time: Optional[str] = None
    session_date: Optional[str] = None
    session_time: Optional[str] = None
    duration_hours: int = 1
    topic: str = ""
    message: str = ""
    notes: str = ""
    mentor_name: Optional[str] = None
    mentor_domain: Optional[str] = None


@router.post("/search")
@router.get("/search")
@router.post("/s/search")
@router.get("/s/search")
async def search_mentors(body: Optional[MentorSearchBody] = None):
    """Search for mentors by expertise, industry, language, etc."""
    try:
        from backend.services.mentor_service import get_mentor_service
        service = get_mentor_service()

        if body is not None:
            expertise_list = body.expertise or ([body.domain] if body.domain else None)
            results = service.search_mentors(
                expertise=expertise_list,
                industry=body.industry,
                language=body.language,
                max_rate=body.max_rate,
                min_rating=body.min_rating or 4.0,
                country=body.country,
            )
        else:
            results = service.search_mentors()

        serializable_results = [
            {
                "mentor_id": m.get("mentor_id", ""),
                "name": m.get("name", ""),
                "title": m.get("title", ""),
                "company": m.get("company", ""),
                "location": m.get("location", ""),
                "country": m.get("country", ""),
                "timezone": m.get("timezone", ""),
                "languages": m.get("languages", []),
                "expertise": m.get("expertise", []),
                "industries": m.get("industries", []),
                "experience_years": m.get("experience_years", 0),
                "hourly_rate": m.get("hourly_rate", 0),
                "currency": m.get("currency", "USD"),
                "bio": m.get("bio", ""),
                "available": m.get("available", True),
                "rating": m.get("rating", 0),
                "total_sessions": m.get("total_sessions", 0),
                "languages_spoken": m.get("languages_spoken", []),
            }
            for m in results
        ]

        return {"mentors": serializable_results}
    except Exception as e:
        logger.error(f"Mentor search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/book")
@router.post("/s/book")
async def book_mentor(body: MentorBookBody):
    """Book a session with a mentor."""
    try:
        from backend.services.mentor_service import get_mentor_service
        service = get_mentor_service()

        if not body.mentor_id:
            raise HTTPException(status_code=400, detail="mentor_id is required")
        if not body.user_id:
            raise HTTPException(status_code=400, detail="user_id is required")

        session_date = body.session_date or body.date
        session_time = body.session_time or body.time

        if not session_date:
            raise HTTPException(status_code=400, detail="session_date is required")
        if not session_time:
            raise HTTPException(status_code=400, detail="session_time is required")

        result = service.book_session(
            user_id=body.user_id,
            mentor_id=body.mentor_id,
            session_date=session_date,
            session_time=session_time,
            duration_hours=body.duration_hours,
            topic=body.topic or body.message,
            notes=body.notes,
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        if "created_at" in result and hasattr(result["created_at"], "isoformat"):
            result["created_at"] = result["created_at"].isoformat()

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Booking error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{user_id}")
async def get_user_sessions(user_id: str):
    """Get user's mentor sessions."""
    try:
        from backend.services.mentor_service import get_mentor_service
        service = get_mentor_service()
        return {"sessions": service.get_user_sessions(user_id)}
    except Exception as e:
        logger.error(f"Sessions error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/domains")
async def mentor_domains():
    """Get available mentor domains."""
    try:
        from backend.services.mentor_service import get_mentor_service
        svc = get_mentor_service()
        if hasattr(svc, "get_domains"):
            return {"domains": svc.get_domains()}
        mentors = svc.search_mentors()
        domains = sorted({d for m in mentors for d in (m.get("expertise") or [])})
        return {"domains": domains}
    except Exception as e:
        logger.error(f"Mentor domains error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))