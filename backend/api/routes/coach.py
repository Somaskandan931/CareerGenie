"""
Job Coach API Routes
====================
Endpoints for AI career coaching chat.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.core.logging import get_logger

logger = get_logger("routes.coach")

router = APIRouter(prefix="/coach", tags=["Coach"])


class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    resume_text: Optional[str] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    response: str


@router.post("/chat", response_model=ChatResponse)
async def job_coach_chat(request: ChatRequest):
    """Chat with the AI career coach."""
    try:
        from backend.services.job_coach import get_job_coach
        coach = get_job_coach()
        response = coach.chat(
            messages=request.messages,
            resume_text=request.resume_text,
        )
        return ChatResponse(reply=response, response=response)
    except Exception as e:
        logger.error(f"Job coach error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/job-coach/chat", response_model=ChatResponse)
async def job_coach_chat_alt(request: ChatRequest):
    """Alternative endpoint for job coach chat (legacy compatibility)."""
    return await job_coach_chat(request)