"""
services/live_session.py
========================
WebRTC signaling server + AI Mock Interview real-time engine.

Handles:
  • Room registry for WebRTC SDP/ICE relay (mentor ↔ candidate)
  • Per-session AI interview state machine
  • LLM-powered question generation and answer evaluation
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Dict, Optional

from fastapi import WebSocket

from backend.config import settings
from backend.services.llm import llm_call_sync, llm_call_smart_sync

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Room registry  (in-memory; replace with Redis for multi-worker deployments)
# ─────────────────────────────────────────────────────────────────────────────
_rooms: Dict[str, Dict[str, WebSocket]] = {}       # room_id → {role: ws}
_interview_state: Dict[str, Dict] = {}             # session_id → state dict


# ─────────────────────────────────────────────────────────────────────────────
# SIGNALING MANAGER
# ─────────────────────────────────────────────────────────────────────────────

class SignalingManager:
    """
    Minimal WebRTC signaling relay.

    Roles: "mentor" | "candidate"
    Message types relayed verbatim: offer, answer, ice, peer_joined, peer_left
    """

    async def join_room(self, room_id: str, role: str, ws: WebSocket) -> None:
        if room_id not in _rooms:
            _rooms[room_id] = {}
        _rooms[room_id][role] = ws
        logger.info(f"[signaling] {role} joined room {room_id}")

        # Notify both peers that the other has arrived
        peer = "candidate" if role == "mentor" else "mentor"
        if peer in _rooms.get(room_id, {}):
            await self._send(ws, {"type": "peer_joined", "role": peer})
            await self._send(_rooms[room_id][peer], {"type": "peer_joined", "role": role})

    async def relay(self, room_id: str, sender_role: str, msg: dict) -> None:
        """Forward a signaling message from sender to the other peer."""
        peer = "candidate" if sender_role == "mentor" else "mentor"
        room = _rooms.get(room_id, {})
        if peer in room:
            await self._send(room[peer], msg)

    async def leave(self, room_id: str, role: str) -> None:
        room = _rooms.get(room_id, {})
        room.pop(role, None)
        logger.info(f"[signaling] {role} left room {room_id}")

        peer = "candidate" if role == "mentor" else "mentor"
        if peer in room:
            await self._send(room[peer], {"type": "peer_left"})

        if not room:
            _rooms.pop(room_id, None)
            logger.info(f"[signaling] room {room_id} closed")

    @staticmethod
    async def _send(ws: WebSocket, data: dict) -> None:
        try:
            await ws.send_text(json.dumps(data))
        except Exception as exc:
            logger.debug(f"[signaling] send failed: {exc}")


signaling = SignalingManager()


# ─────────────────────────────────────────────────────────────────────────────
# AI INTERVIEW ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class AIInterviewEngine:
    """
    Stateful interview engine per session_id.

    Flow:
        start_session()      →  first question
        next_question(ans)   →  evaluate answer + next question (or summary)
        evaluate_transcript()→  evaluate only, no state advance
    """

    # ── Session lifecycle ─────────────────────────────────────────────────────

    def start_session(
        self,
        session_id: str,
        role: str,
        interview_type: str,
        resume_text: str = "",
        num_questions: int = 10,
    ) -> dict:
        _interview_state[session_id] = {
            "session_id": session_id,
            "role": role,
            "interview_type": interview_type,
            "resume_text": resume_text[:600],
            "num_questions": num_questions,
            "history": [],           # [{question, answer, feedback}]
            "q_index": 0,
            "scores": [],
            "current_question": "",
        }
        first_q = self._generate_question(session_id, is_first=True)
        logger.info(f"[interview] session {session_id} started — {role} / {interview_type}")
        return {
            "session_id": session_id,
            "question": first_q,
            "q_index": 0,
            "total_questions": num_questions,
        }

    def next_question(self, session_id: str, transcript: str) -> dict:
        """Evaluate the answer to the current question, then advance."""
        state = _interview_state.get(session_id)
        if not state:
            return {"error": "Session not found. Call /interview/live/start first."}

        feedback = self._evaluate(state, transcript)
        state["history"].append({
            "question": state["current_question"],
            "answer": transcript,
            "feedback": feedback,
        })
        state["scores"].append(feedback.get("score", 5))
        state["q_index"] += 1

        if state["q_index"] >= state["num_questions"]:
            summary = self._build_summary(state)
            logger.info(f"[interview] session {session_id} complete — avg {summary['average_score']}")
            return {"done": True, "feedback": feedback, "summary": summary}

        next_q = self._generate_question(session_id)
        return {
            "done": False,
            "question": next_q,
            "feedback": feedback,
            "q_index": state["q_index"],
        }

    def evaluate_transcript(self, session_id: str, transcript: str) -> dict:
        """Quick evaluation without advancing state."""
        state = _interview_state.get(session_id)
        if not state:
            return {"error": "Session not found."}
        return self._evaluate(state, transcript)

    # ── Internals ─────────────────────────────────────────────────────────────

    def _generate_question(self, session_id: str, is_first: bool = False) -> str:
        state = _interview_state[session_id]

        history_ctx = ""
        if state["history"]:
            recent = state["history"][-4:]
            history_ctx = "Previous questions asked (DO NOT repeat):\n" + "\n".join(
                f"  Q{i+1}: {h['question']}" for i, h in enumerate(recent)
            )

        resume_ctx = (
            f"Candidate background (from resume):\n{state['resume_text']}\n"
            if state["resume_text"] else ""
        )

        prompt = (
            f"You are conducting a {state['interview_type']} mock interview for the role: "
            f"\"{state['role']}\".\n"
            f"{resume_ctx}"
            f"{history_ctx}\n\n"
            f"Generate {'the opening' if is_first else 'the next'} interview question.\n"
            "Rules:\n"
            "- Output ONLY the question text, nothing else\n"
            "- No numbering, no prefix\n"
            "- Make it specific and relevant to the role\n"
            "- Vary between conceptual, situational, and behavioural depending on type\n"
            "- Keep it to 1-2 sentences"
        )

        try:
            question = llm_call_sync(
                system=(
                    "You are a professional senior interviewer. "
                    "Output only the interview question. No preamble, no numbering."
                ),
                user=prompt,
                temp=0.75,
                max_tokens=120,
            ).strip().strip('"')
        except Exception as e:
            logger.error(f"Question generation error: {e}")
            # Fallback question
            question = f"Tell me about your experience with {state['role']} and why you're interested in this role."

        state["current_question"] = question
        return question

    def _evaluate(self, state: dict, answer: str) -> dict:
        prompt = (
            f"Evaluate the following interview answer.\n\n"
            f"Role: {state['role']}\n"
            f"Interview type: {state['interview_type']}\n"
            f"Question: {state['current_question']}\n"
            f"Candidate's answer: {answer}\n\n"
            "Respond with ONLY valid JSON (no markdown, no backticks):\n"
            "{\n"
            '  "score": <integer 1-10>,\n'
            '  "strengths": ["<specific strength 1>", "<specific strength 2>"],\n'
            '  "improvements": ["<specific improvement 1>", "<specific improvement 2>"],\n'
            '  "sample_better_answer": "<a concise model answer in 2-3 sentences>",\n'
            '  "next_question_hint": "<brief topic hint for next question>"\n'
            "}"
        )

        try:
            raw = llm_call_sync(
                system=(
                    "You are an expert interviewer and evaluator. "
                    "Respond with valid JSON only. No markdown code blocks."
                ),
                user=prompt,
                temp=0.3,
                max_tokens=500,
            )
            raw = raw.strip()
            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            result = json.loads(raw.strip())
            return result
        except Exception as exc:
            logger.error(f"[interview] evaluate parse error: {exc}")
            return {
                "score": 5,
                "strengths": ["Answer received"],
                "improvements": ["Could not parse detailed feedback — try a longer answer"],
                "sample_better_answer": "",
                "next_question_hint": "",
            }

    @staticmethod
    def _build_summary(state: dict) -> dict:
        scores = state["scores"]
        avg = round(sum(scores) / max(len(scores), 1), 1)
        return {
            "average_score": avg,
            "total_questions": len(state["history"]),
            "scores_per_question": scores,
            "performance": (
                "Excellent" if avg >= 8 else
                "Good" if avg >= 6 else
                "Needs Practice"
            ),
            "role": state["role"],
            "interview_type": state["interview_type"],
        }


interview_engine = AIInterviewEngine()