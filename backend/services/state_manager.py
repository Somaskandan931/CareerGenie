"""
core/state_manager.py
======================
Session-based persistent state manager.

Sits above AgentMemory (which is per-orchestrator-instance, i.e. per request).
StateManager survives across requests in the same process — it tracks
per-session history, user preferences, and accumulated context so the system
can reference previous queries and build a richer picture of the user over time.

Design:
  - In-process dict keyed by session_id (survives process lifetime)
  - Each session stores: history[], preferences{}, agent_outputs{}
  - Serialisable to JSON so it can be persisted to disk / Redis later
  - Thread-safe reads; writes use a simple lock

Differences from AgentMemory:
  • AgentMemory  — per-request scratchpad, cleared after each orchestrator run
  • StateManager — cross-request session store, grows over the session lifetime
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_DEFAULT_SESSION: Dict = {
    "history":        [],   # list of {query, final_answer, confidence, ts}
    "preferences":    {},   # user-stated or inferred preferences
    "agent_outputs":  {},   # latest output per agent type
    "resume_text":    "",
    "target_role":    "",
    "created_at":     None,
    "last_active":    None,
}


class StateManager:
    """
    Cross-request session memory.

    Usage:
        session = state.get("sess_abc123")
        state.update("sess_abc123", {"query": "...", "final": "...", "confidence": 0.82})
        state.set_preference("sess_abc123", "location", "Bangalore")
        state.set_agent_output("sess_abc123", "JobAgent", {...})
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, Dict] = {}
        self._lock = threading.Lock()

    # ── Session lifecycle ──────────────────────────────────────────────────────

    def get(self, session_id: str) -> Dict:
        """Return the session dict, creating it if it doesn't exist."""
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = {
                    **_DEFAULT_SESSION,
                    "created_at":  time.time(),
                    "last_active": time.time(),
                }
            return self._sessions[session_id]

    def update(self, session_id: str, data: Dict) -> None:
        """
        Append a history record and update last_active.

        data should contain at minimum: {query, final, confidence}
        """
        session = self.get(session_id)
        with self._lock:
            record = {
                "ts":         time.time(),
                "query":      data.get("query", ""),
                "final":      data.get("final", ""),
                "confidence": data.get("confidence", 0.0),
                **{k: v for k, v in data.items() if k not in ("query", "final", "confidence")},
            }
            session["history"].append(record)
            session["last_active"] = time.time()
            # Cap history at 50 records to avoid unbounded growth
            if len(session["history"]) > 50:
                session["history"] = session["history"][-50:]

    def set_preference(self, session_id: str, key: str, value: Any) -> None:
        session = self.get(session_id)
        with self._lock:
            session["preferences"][key] = value

    def set_agent_output(self, session_id: str, agent_name: str, output: Any) -> None:
        session = self.get(session_id)
        with self._lock:
            session["agent_outputs"][agent_name] = output

    def set_resume(self, session_id: str, resume_text: str, target_role: str = "") -> None:
        session = self.get(session_id)
        with self._lock:
            session["resume_text"] = resume_text
            if target_role:
                session["target_role"] = target_role

    # ── Accessors ──────────────────────────────────────────────────────────────

    def history(self, session_id: str, last_n: int = 5) -> List[Dict]:
        return self.get(session_id)["history"][-last_n:]

    def preferences(self, session_id: str) -> Dict:
        return self.get(session_id).get("preferences", {})

    def resume(self, session_id: str) -> str:
        return self.get(session_id).get("resume_text", "")

    def target_role(self, session_id: str) -> str:
        return self.get(session_id).get("target_role", "")

    def active_sessions(self) -> List[str]:
        return list(self._sessions.keys())

    def drop(self, session_id: str) -> None:
        """Explicitly expire a session."""
        with self._lock:
            self._sessions.pop(session_id, None)

    def snapshot(self, session_id: str) -> Dict:
        """Return a serialisable copy of the session (safe to JSON-encode)."""
        session = self.get(session_id)
        with self._lock:
            return {
                "session_id":    session_id,
                "created_at":    session.get("created_at"),
                "last_active":   session.get("last_active"),
                "history_count": len(session.get("history", [])),
                "recent_history": session.get("history", [])[-3:],
                "preferences":   session.get("preferences", {}),
                "target_role":   session.get("target_role", ""),
                "resume_loaded": bool(session.get("resume_text")),
            }


# ── Module-level singleton ─────────────────────────────────────────────────────
# Import this instance wherever cross-request memory is needed:
#   from backend.services.state_manager import state

state = StateManager()
