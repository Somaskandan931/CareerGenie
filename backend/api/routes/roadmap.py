"""
Roadmap API Routes
==================
Endpoints for learning path generation and project suggestions.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.core.logging import get_logger
from backend.services.roadmap_generator import get_roadmap_generator
from backend.services.project_generator import get_project_generator
from backend.services.enhanced_skill_extractor import EnhancedSkillExtractor

logger = get_logger("routes.roadmap")

router = APIRouter(prefix="/roadmap", tags=["Roadmap"])


class RoadmapRequest(BaseModel):
    resume_text: str
    target_role: str
    skill_gaps: Optional[List[str]] = None
    duration_weeks: int = 12


class RoadmapResponse(BaseModel):
    roadmap: dict
    _confidence: dict = {}


class ProjectRequest(BaseModel):
    resume_text: str
    target_role: str
    skill_gaps: Optional[List[str]] = None
    difficulty: Optional[str] = "intermediate"
    num_projects: int = 5


class ProjectResponse(BaseModel):
    projects: list


class DeepAnalysisRequest(BaseModel):
    resume_text: str
    target_role: str = "Software Engineer"
    duration_weeks: int = 12


@router.post("/generate", response_model=RoadmapResponse)
async def generate_roadmap(request: RoadmapRequest):
    """Generate personalized learning roadmap."""
    try:
        skill_gaps = request.skill_gaps
        if not skill_gaps:
            extractor = EnhancedSkillExtractor()
            skills = extractor.extract_skills_with_context(request.resume_text)
            skill_gaps = [s["skill"] for s in skills[:5]] if skills else ["Python", "SQL", "System Design"]

        generator = get_roadmap_generator()
        roadmap = generator.generate_roadmap(
            request.resume_text,
            request.target_role,
            skill_gaps,
            request.duration_weeks,
        )

        return RoadmapResponse(roadmap=roadmap)
    except Exception as e:
        logger.error(f"Roadmap generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/suggest", response_model=ProjectResponse)
async def suggest_projects(request: ProjectRequest):
    """Suggest portfolio projects based on skill gaps."""
    try:
        generator = get_project_generator()
        projects = generator.suggest_projects(
            resume_text=request.resume_text,
            target_role=request.target_role,
            skill_gaps=request.skill_gaps or [],
            difficulty=request.difficulty,
            num_projects=request.num_projects,
        )
        return ProjectResponse(projects=projects)
    except Exception as e:
        logger.error(f"Project suggestion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deep-analysis")
async def career_deep_analysis(request: DeepAnalysisRequest):
    """
    4-node LangGraph flow: parse_resume → gap_analysis → generate_roadmap → suggest_projects
    """
    try:
        from backend.services.langgraph_career_flow import run_deep_analysis
        result = run_deep_analysis(
            resume_text=request.resume_text,
            target_role=request.target_role,
            duration_weeks=request.duration_weeks,
        )
        return result
    except Exception as e:
        logger.error(f"Deep analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))