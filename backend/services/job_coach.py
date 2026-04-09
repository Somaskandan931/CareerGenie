import google.genai as genai
"""
Job Coach / Career Counsellor chatbot service.
Maintains conversation history per session and answers career questions
using the candidate's resume as context.
"""
from typing import List, Dict, Optional
import logging

from backend.config import settings

_genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)

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
        pass

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
            response = _genai_client.models.generate_content(
                model=settings.GEMINI_CHAT_MODEL,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system,
                    temperature=0.7,
                    max_output_tokens=settings.MAX_TOKENS_CHAT,
                ),
                contents=prompt,
        )
            return response.text.strip()
        except Exception as e:
            logger.error(f"JobCoach error: {e}")
            raise Exception(f"Job coach unavailable: {str(e)}")


_job_coach = None

def get_job_coach() -> JobCoach:
    global _job_coach
    if _job_coach is None:
        _job_coach = JobCoach()
    return _job_coach