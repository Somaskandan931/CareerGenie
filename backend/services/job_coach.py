"""
Job Coach / Career Counsellor chatbot service.
Maintains conversation history per session and answers career questions
using the candidate's resume as context.
"""
from groq import Groq
from typing import List, Dict, Optional
import logging

from backend.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an experienced, empathetic career coach and counsellor named "Genie".
You help job seekers with:
- Career decisions and role transitions
- Resume and cover letter advice
- Salary negotiation strategies
- Interview preparation tips
- How to approach skill gaps
- Job search strategies and networking
- Work-life balance and career growth planning

You are supportive, direct, and practical. Give specific, actionable advice.
When the user shares their resume or background, personalise your advice to their situation.
Keep responses concise (3-5 sentences unless a detailed explanation is needed).
Never make up job listings or company-specific salary data — give ranges instead."""


class JobCoach:
    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not configured")
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        logger.info("JobCoach initialized with Groq")

    def chat(self, messages: List[Dict], resume_text: Optional[str] = None) -> str:
        """
        Send a message to the job coach.

        Args:
            messages: List of {"role": "user"|"assistant", "content": str}
            resume_text: Optional resume context to include in system prompt

        Returns:
            Coach's reply as a string
        """
        system = SYSTEM_PROMPT
        if resume_text and resume_text.strip():
            system += f"\n\nCandidate's resume context:\n{resume_text[:1500]}"

        try:
            response = self.client.chat.completions.create(
                model=settings.GROQ_CHAT_MODEL,
                max_tokens=settings.MAX_TOKENS_CHAT,
                messages=[{"role": "system", "content": system}] + messages
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"JobCoach error: {e}")
            raise Exception(f"Job coach unavailable: {str(e)}")


_job_coach = None

def get_job_coach() -> JobCoach:
    global _job_coach
    if _job_coach is None:
        _job_coach = JobCoach()
    return _job_coach