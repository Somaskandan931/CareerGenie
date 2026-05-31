"""
Market Insights API Routes
==========================
Endpoints for market insights and skill analysis.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.core.logging import get_logger

logger = get_logger("routes.insights")

router = APIRouter(prefix="/insights", tags=["Insights"])


class MarketInsightsRequest(BaseModel):
    role: str
    skills: Optional[List[str]] = None
    location: str = "India"


class SkillExtractRequest(BaseModel):
    text: str
    enhanced: bool = True


class SkillsGapRequest(BaseModel):
    resume_text: str
    job_description: str


@router.post("/market")
@router.get("/market")
@router.post("/market-insights")
@router.get("/market-insights")
async def market_insights(
    request: Optional[MarketInsightsRequest] = None,
    role: Optional[str] = None,
    skills: Optional[str] = None,
    location: str = "India",
):
    """Get market insights for a role and skills."""
    try:
        from backend.services.market_insights import get_market_insights
        insights = get_market_insights()

        if request is not None:
            _role = request.role
            _skills = request.skills
            _location = request.location
        else:
            _role = role or "Software Engineer"
            _skills = skills.split(",") if skills else None
            _location = location

        return insights.get_insights(_role, _skills, _location)
    except Exception as e:
        logger.error(f"Market insights error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/skills/extract")
async def extract_skills(text: str, enhanced: bool = True):
    """Extract skills from text."""
    try:
        from backend.services.enhanced_skill_extractor import EnhancedSkillExtractor
        extractor = EnhancedSkillExtractor()
        skills = extractor.extract_skills_with_context(text)
        return {"skills": skills}
    except Exception as e:
        logger.error(f"Skill extraction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/skills/gap")
async def skills_gap_endpoint(resume_text: str, job_description: str):
    """Analyze skill gaps between resume and job description."""
    try:
        from backend.services.enhanced_skill_extractor import EnhancedSkillExtractor
        extractor = EnhancedSkillExtractor()
        resume_skills = extractor.extract_skills_with_context(resume_text)
        job_skills = extractor.extract_skills_with_context(job_description)
        comparison = extractor.compare_skills(resume_skills, job_skills)
        return comparison
    except Exception as e:
        logger.error(f"Skills gap error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))