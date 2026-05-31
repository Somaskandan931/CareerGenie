"""
Admin API Routes
================
Administrative endpoints for system management.
"""

from typing import Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.core.logging import get_logger

logger = get_logger("routes.admin")

router = APIRouter(prefix="/admin", tags=["Admin"])


class TNBatchAnalyticsRequest(BaseModel):
    institution_name: Optional[str] = None
    profiles: list


@router.get("/config")
async def get_config():
    """Return frontend configuration."""
    try:
        from backend.core.config import settings

        def _check_ollama() -> bool:
            try:
                from backend.services.ollama_service import get_ollama_service
                return get_ollama_service().available
            except Exception:
                return False

        # Frontend uses these flags to show banners like
        # "Groq API key missing".
        import os
        groq_key      = settings.GROQ_API_KEY      or os.environ.get("GROQ_API_KEY")
        anthropic_key = settings.ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY")
        gemini_key    = settings.GEMINI_API_KEY    or os.environ.get("GEMINI_API_KEY")
        ollama_ok     = _check_ollama()
        return {
            "ollama_available": ollama_ok,
            "serpapi_key_present": bool(settings.effective_serpapi_key),
            "groq_key_present": bool(groq_key),
            "anthropic_key_present": bool(anthropic_key),
            "gemini_key_present": bool(gemini_key),
            "any_llm_available": ollama_ok or bool(groq_key) or bool(anthropic_key) or bool(gemini_key),
            "features": {
                "debate": True,
                "live_interview": True,
                "mentor_matching": True,
                "progress_tracking": True,
            },
        }
    except Exception as e:
        logger.error(f"Config error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orchestrator/run")
async def orchestrator_run(goal: str, user_id: str = "", extra_context: Optional[Dict] = None):
    """Run agent orchestrator for complex multi-step tasks."""
    try:
        from backend.services.agent_orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        return orchestrator.run_goal(goal=goal, user_id=user_id, extra_context=extra_context)
    except Exception as e:
        logger.error(f"Orchestrator error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orchestrator/plan")
async def orchestrator_plan(user_intent: str, user_id: str = ""):
    """Plan tasks from user intent."""
    try:
        from backend.services.agent_orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        return orchestrator.plan_from_intent(user_intent, user_id)
    except Exception as e:
        logger.error(f"Planning error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/debate/run")
async def debate_run(topic: str, context: Dict, max_rounds: int = 2, resume_text: Optional[str] = None, user_id: Optional[str] = None):
    """Run multi-agent debate for career recommendations."""
    try:
        from backend.services.agent_debate import get_debate_orchestrator
        debate = get_debate_orchestrator()
        result = debate.run_debate(
            topic=topic,
            context=context,
            max_rounds=max_rounds,
            resume_text=resume_text,
            user_id=user_id,
        )
        return debate.to_dict(result)
    except Exception as e:
        logger.error(f"Debate error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/debate/quick-critique")
async def quick_critique(plan: Dict, context: Dict):
    """Quick single-round critique of a plan."""
    try:
        from backend.services.agent_debate import get_debate_orchestrator
        debate = get_debate_orchestrator()
        result = debate.quick_critique(plan, context)
        return result
    except Exception as e:
        logger.error(f"Critique error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tn/batch-analytics")
async def tn_batch_analytics(request: TNBatchAnalyticsRequest):
    """Batch analytics for TN Automotive taxonomy."""
    try:
        from backend.services.tn_automotive_taxonomy import TNAutomotiveSkillExtractor
        taxonomy = TNAutomotiveSkillExtractor()
        result = taxonomy.batch_analyze(request.profiles)
        if request.institution_name:
            result["institution_name"] = request.institution_name
        return result
    except Exception as e:
        logger.error(f"TN batch analytics error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tn-automotive/roles")
async def tn_automotive_roles():
    """Get TN Automotive taxonomy roles."""
    try:
        from backend.services.tn_automotive_taxonomy import tn_extractor
        return {"roles": tn_extractor.list_roles()}
    except Exception as e:
        logger.error(f"Roles error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tn-automotive/extract-skills")
async def tn_automotive_extract_skills(text: str):
    """Extract skills using TN Automotive taxonomy."""
    try:
        from backend.services.tn_automotive_taxonomy import tn_extractor
        return {"skills": tn_extractor.extract_skills(text)}
    except Exception as e:
        logger.error(f"Extract error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tn-automotive/gap-analysis")
async def tn_automotive_gap_analysis(text: str, role_name: str):
    """Analyze skill gaps using TN Automotive taxonomy."""
    try:
        from backend.services.tn_automotive_taxonomy import tn_extractor
        skills = tn_extractor.extract_skills(text)
        return tn_extractor.get_skill_gaps_for_role(skills, role_name)
    except Exception as e:
        logger.error(f"Gap analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))