"""
services/job_coach.py  —  Stateless conversational career coach ("Genie")
=========================================================================
Uses llm.py — never calls any LLM SDK directly.
Provider waterfall handled automatically: Groq → Anthropic → Gemini
"""

from __future__ import annotations

import logging
from typing import List, Dict, Optional

from backend.services.llm import llm_call_sync
from backend.config import settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are Genie, an expert AI career coach specialising in
the Indian job market — especially tech, automotive, EV, and manufacturing roles
in Tamil Nadu and across India.

Your job is to give specific, actionable career advice. Guidelines:
- Be direct and practical. No generic platitudes.
- Tailor every answer to the candidate's resume and situation when provided.
- Cover: resume tips, salary negotiation, skill gaps, role transitions,
  interview prep, job search strategy, LinkedIn optimisation.
- Keep replies to 3-5 sentences unless the question genuinely needs more depth.
- Use bullet points only when listing steps or options — otherwise use prose.
- Never say "I cannot help with that." Always give the best answer you can.
- If the resume is provided, reference specific skills or experience from it.
"""


class JobCoach:
    def chat(
        self,
        messages:    List[Dict[str, str]],
        resume_text: Optional[str] = None,
    ) -> str:
        if not messages:
            raise ValueError("messages list is empty")

        context_parts = []
        if resume_text and resume_text.strip():
            context_parts.append(
                f"Candidate resume (excerpt):\n{resume_text.strip()[:1500]}"
            )

        history_lines = []
        for m in messages[:-1]:
            role = "Candidate" if m["role"] == "user" else "Genie"
            history_lines.append(f"{role}: {m['content']}")
        if history_lines:
            context_parts.append("Conversation so far:\n" + "\n".join(history_lines))

        system = _SYSTEM_PROMPT
        if context_parts:
            system += "\n\n--- Context ---\n" + "\n\n".join(context_parts)

        # Retry logic
        for attempt in range(3):
            try:
                return llm_call_sync(
                    system=system,
                    user=messages[-1]["content"],
                    temp=0.7,
                    max_tokens=settings.MAX_TOKENS_CHAT,
                )
            except Exception as exc:
                logger.error(f"JobCoach attempt {attempt + 1} error: {exc}")
                if attempt < 2:
                    import time
                    time.sleep(2 ** attempt)
                else:
                    raise Exception(f"Unable to generate response after 3 attempts: {exc}")


_instance: Optional[JobCoach] = None


def get_job_coach() -> JobCoach:
    global _instance
    if _instance is None:
        _instance = JobCoach()
        logger.info("[job_coach] ready — Groq → Anthropic → Gemini")
    return _instance