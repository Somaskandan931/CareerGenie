"""
Interview API Routes
====================
Endpoints for interview preparation and HR panel evaluation.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.core.logging import get_logger

logger = get_logger("routes.interview")

router = APIRouter(prefix="/interview", tags=["Interview"])


class InterviewRequest(BaseModel):
    role: str
    interview_type: str = "mixed"
    resume_text: Optional[str] = None
    num_questions: int = 10


class InterviewAnswerRequest(BaseModel):
    question: str
    answer: str
    role: str
    interview_type: str = "mixed"


class HRPanelRequest(BaseModel):
    resume_text: str
    target_role: str = "Software Engineer"
    company_type: Optional[str] = None
    focus_area: Optional[str] = None


class LiveInterviewStartRequest(BaseModel):
    role: str
    interview_type: str = "mixed"
    resume_text: str = ""
    num_questions: int = 10


class LiveInterviewNextRequest(BaseModel):
    session_id: str
    transcript: str


@router.post("/generate-questions")
async def interview_questions(request: InterviewRequest):
    """Generate interview questions for a role."""
    try:
        from backend.services.interview_coach import get_interview_coach
        coach = get_interview_coach()
        questions = coach.generate_questions(
            role=request.role,
            interview_type=request.interview_type,
            resume_text=request.resume_text,
            num_questions=request.num_questions,
        )
        return {"questions": questions}
    except Exception as e:
        logger.error(f"Question generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate-answer")
async def evaluate_answer(request: InterviewAnswerRequest):
    """Evaluate an interview answer."""
    try:
        from backend.services.interview_coach import get_interview_coach
        coach = get_interview_coach()
        result = coach.evaluate_answer(
            question=request.question,
            answer=request.answer,
            role=request.role,
            interview_type=request.interview_type,
        )
        return result
    except Exception as e:
        logger.error(f"Answer evaluation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hr-panel")
async def hr_panel_endpoint(request: HRPanelRequest):
    """Generate HR-style evaluation of a resume."""
    try:
        from backend.api.routes.resume import _generate_hr_panel
        panel = _generate_hr_panel(
            resume_text=request.resume_text,
            target_role=request.target_role,
            company_type=request.company_type,
            focus_area=request.focus_area,
            num_questions=10,
        )
        return {"panel": panel}
    except Exception as e:
        logger.error(f"HR panel error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/live/start")
async def live_interview_start(request: LiveInterviewStartRequest):
    """Start a live interview session."""
    try:
        from backend.services.live_session import interview_engine
        import uuid
        session_id = str(uuid.uuid4())
        return interview_engine.start_session(
            session_id=session_id,
            role=request.role,
            interview_type=request.interview_type,
            resume_text=request.resume_text,
            num_questions=request.num_questions,
        )
    except Exception as e:
        logger.error(f"Live interview start error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/live/next")
async def live_interview_next(request: LiveInterviewNextRequest):
    """Get next question in live interview session."""
    try:
        from backend.services.live_session import interview_engine
        return interview_engine.next_question(
            session_id=request.session_id,
            transcript=request.transcript,
        )
    except Exception as e:
        logger.error(f"Live interview next error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))