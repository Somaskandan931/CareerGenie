"""
Interview Live Routes
=====================
WebRTC-based live mock interview endpoints.
"""

from __future__ import annotations

import json
import logging
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional

from backend.services.live_session import signaling, interview_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interview/live", tags=["interview-live"])


class StartSessionRequest(BaseModel):
    role: str
    interview_type: str = "mixed"
    resume_text: str = ""
    num_questions: int = 10


class StartSessionResponse(BaseModel):
    session_id: str
    question: str
    q_index: int
    total_questions: int


class AnswerRequest(BaseModel):
    session_id: str
    answer: str


class AnswerResponse(BaseModel):
    done: bool
    question: Optional[str] = None
    feedback: Optional[Dict] = None
    summary: Optional[Dict] = None
    q_index: int


@router.post("/start", response_model=StartSessionResponse)
async def start_session(request: StartSessionRequest):
    """Start a new live interview session."""
    session_id = str(uuid.uuid4())[:8]

    result = interview_engine.start_session(
        session_id=session_id,
        role=request.role,
        interview_type=request.interview_type,
        resume_text=request.resume_text,
        num_questions=request.num_questions,
    )

    return StartSessionResponse(**result)


@router.post("/answer", response_model=AnswerResponse)
async def submit_answer(request: AnswerRequest):
    """Submit an answer and get the next question."""
    result = interview_engine.next_question(request.session_id, request.answer)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return AnswerResponse(
        done=result.get("done", False),
        question=result.get("question"),
        feedback=result.get("feedback"),
        summary=result.get("summary"),
        q_index=result.get("q_index", 0),
    )


@router.post("/evaluate")
async def evaluate_transcript(request: AnswerRequest):
    """Evaluate an answer without advancing the session."""
    result = interview_engine.evaluate_transcript(request.session_id, request.answer)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.websocket("/ws/{session_id}/{role}")
async def websocket_interview(websocket: WebSocket, session_id: str, role: str):
    """
    WebSocket endpoint for real-time interview.
    role: "mentor" or "candidate"
    """
    if role not in ("mentor", "candidate"):
        await websocket.close(code=1008, reason="Invalid role")
        return

    await websocket.accept()
    await signaling.join_room(session_id, role, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            msg_type = message.get("type")

            if msg_type == "offer":
                await signaling.relay(session_id, role, {
                    "type": "offer",
                    "sdp": message.get("sdp"),
                    "from": role,
                })

            elif msg_type == "answer":
                await signaling.relay(session_id, role, {
                    "type": "answer",
                    "sdp": message.get("sdp"),
                    "from": role,
                })

            elif msg_type == "ice-candidate":
                await signaling.relay(session_id, role, {
                    "type": "ice-candidate",
                    "candidate": message.get("candidate"),
                    "from": role,
                })

            elif msg_type == "chat":
                await signaling.relay(session_id, role, {
                    "type": "chat",
                    "message": message.get("message"),
                    "from": role,
                })

            elif msg_type == "end-interview":
                await signaling.relay(session_id, role, {"type": "end-interview", "from": role})

            else:
                logger.warning(f"Unknown message type: {msg_type}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}/{role}")
        await signaling.leave(session_id, role)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await signaling.leave(session_id, role)