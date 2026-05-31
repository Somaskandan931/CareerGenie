"""
backend/services/job_coach.py  —  Stateless conversational career coach ("Genie")
==================================================================================
Refactored to:
  - Route all LLM calls through ``backend.core.ai_pipeline``
  - Use centralized system prompt from ``backend.core.prompts``
  - Sanitize user-supplied resume text
  - Use structured logging via ``backend.core.logging``
"""
from __future__ import annotations

from typing import Dict, List, Optional

from backend.core import ai_pipeline
from backend.core.config import settings
from backend.core.exceptions import LLMUnavailableError
from backend.core.logging import get_logger
from backend.core.prompts import Prompts

logger = get_logger("job_coach")


class JobCoach:
    def chat(
        self,
        messages: List[Dict[str, str]],
        resume_text: Optional[str] = None,
    ) -> str:
        if not messages:
            raise ValueError("messages list is empty")

        safe_resume = (
            ai_pipeline.sanitize_user_content(resume_text, max_length=1500)
            if resume_text and resume_text.strip()
            else None
        )

        system = Prompts.job_coach_system(safe_resume)

        # Append conversation history as context block
        history_lines = []
        for m in messages[:-1]:
            role = "Candidate" if m["role"] == "user" else "Genie"
            history_lines.append(f"{role}: {m['content']}")
        if history_lines:
            system += "\n\n--- Conversation so far ---\n" + "\n".join(history_lines)

        for attempt in range(3):
            try:
                return ai_pipeline.call(
                    system=system,
                    user=messages[-1]["content"],
                    temp=0.7,
                    max_tokens=settings.MAX_TOKENS_CHAT,
                    use_cache=False,
                )
            except LLMUnavailableError as exc:
                logger.error("JobCoach attempt %d LLM unavailable: %s", attempt + 1, exc)
                if attempt < 2:
                    import time
                    time.sleep(2 ** attempt)
                else:
                    raise Exception(f"Unable to generate response after 3 attempts: {exc}")
            except Exception as exc:
                logger.error("JobCoach attempt %d error: %s", attempt + 1, exc)
                if attempt < 2:
                    import time
                    time.sleep(2 ** attempt)
                else:
                    raise Exception(f"Unable to generate response after 3 attempts: {exc}")


# ── Singleton ──────────────────────────────────────────────────────────────────

_instance: Optional[JobCoach] = None


def get_job_coach() -> JobCoach:
    global _instance
    if _instance is None:
        _instance = JobCoach()
        logger.info("[job_coach] ready — Ollama → Groq → Anthropic")
    return _instance
