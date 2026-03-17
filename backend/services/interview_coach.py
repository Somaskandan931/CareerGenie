"""
AI Interview Coach service.
Conducts mock interviews, evaluates answers, and provides structured feedback.
Supports technical, behavioural, and HR interview modes.
"""
from groq import Groq
from typing import List, Dict, Optional
import logging
import json
import re

from backend.config import settings

logger = logging.getLogger(__name__)

INTERVIEWER_SYSTEM = """You are a professional interviewer conducting a mock job interview.
Your job is to:
1. Ask realistic interview questions suited to the role and interview type
2. Evaluate the candidate's answer when they provide one
3. Give constructive, specific feedback
4. Stay in character as a professional interviewer throughout

Interview types:
- technical: coding, system design, architecture, domain knowledge
- behavioural: STAR-format questions about past experience
- hr: culture fit, motivation, salary, career goals

Rules:
- Ask ONE question at a time
- After each answer, give brief feedback (2-3 sentences) then ask the next question
- Be encouraging but honest — point out weak answers constructively
- Vary question difficulty progressively
- Track the conversation and don't repeat questions"""


class InterviewCoach:
    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not configured")
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        logger.info("InterviewCoach initialized with Groq")

    def generate_questions(self, role: str, interview_type: str = "mixed",
                            resume_text: Optional[str] = None,
                            num_questions: int = 10) -> List[Dict]:
        """
        Pre-generate a bank of interview questions for a role.

        Args:
            role: Target job role
            interview_type: "technical" | "behavioural" | "hr" | "mixed"
            resume_text: Optional resume for personalised questions
            num_questions: Number of questions to generate

        Returns:
            List of {question, type, difficulty, hints, ideal_answer_points}
        """
        prompt = f"""Generate {num_questions} interview questions for a "{role}" position.
Interview type: {interview_type}
{'Candidate background: ' + resume_text[:600] if resume_text else ''}

Respond ONLY with a valid JSON array:
[
  {{
    "id": 1,
    "question": "<the interview question>",
    "type": "technical|behavioural|hr",
    "difficulty": "easy|medium|hard",
    "hints": "<1 sentence hint for the candidate>",
    "ideal_answer_points": ["<key point 1>", "<key point 2>", "<key point 3>"]
  }}
]

Mix difficulty levels. Make questions specific to the role. No duplicates."""

        try:
            response = self.client.chat.completions.create(
                model=settings.GROQ_SMART_MODEL,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response.choices[0].message.content.strip()
            raw = re.sub(r"^```json\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            return json.loads(raw)
        except Exception as e:
            logger.error(f"Question generation error: {e}")
            return self._fallback_questions(role, num_questions)

    def evaluate_answer(self, question: str, answer: str, role: str,
                         interview_type: str = "mixed") -> Dict:
        """
        Evaluate a candidate's answer and return structured feedback.

        Returns:
            {score: int (0-10), strengths: [str], improvements: [str],
             sample_better_answer: str, follow_up_question: str}
        """
        prompt = f"""You are evaluating a candidate's interview answer for a "{role}" position.

Question: {question}
Candidate's answer: {answer}
Interview type: {interview_type}

Respond ONLY with a valid JSON object:
{{
  "score": <integer 0-10>,
  "strengths": ["<what they did well>", "<another strength>"],
  "improvements": ["<specific improvement>", "<another improvement>"],
  "sample_better_answer": "<a concise model answer in 2-3 sentences>",
  "follow_up_question": "<a follow-up question based on their answer>"
}}

Be fair, specific, and constructive."""

        try:
            response = self.client.chat.completions.create(
                model=settings.GROQ_SMART_MODEL,
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response.choices[0].message.content.strip()
            raw = re.sub(r"^```json\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            return json.loads(raw)
        except Exception as e:
            logger.error(f"Answer evaluation error: {e}")
            return {
                "score": 5, "strengths": ["Attempted the question"],
                "improvements": ["Provide more specific examples", "Structure your answer using STAR method"],
                "sample_better_answer": "Unable to generate sample answer at this time.",
                "follow_up_question": "Can you elaborate on that point?"
            }

    def chat(self, messages: List[Dict], role: str, interview_type: str = "mixed",
              resume_text: Optional[str] = None) -> str:
        """
        Conduct a live mock interview via back-and-forth chat.

        Args:
            messages: Conversation history
            role: Target job role
            interview_type: "technical" | "behavioural" | "hr" | "mixed"
            resume_text: Optional resume context

        Returns:
            Interviewer's next message
        """
        system = INTERVIEWER_SYSTEM
        system += f"\n\nRole being interviewed for: {role}"
        system += f"\nInterview type: {interview_type}"
        if resume_text:
            system += f"\nCandidate's background: {resume_text[:800]}"

        # If this is the first message (no prior assistant turn), start the interview
        if not any(m["role"] == "assistant" for m in messages):
            system += "\n\nStart with a brief welcome, explain the format, then ask your first question."

        try:
            response = self.client.chat.completions.create(
                model=settings.GROQ_SMART_MODEL,
                max_tokens=settings.MAX_TOKENS_CHAT,
                messages=[{"role": "system", "content": system}] + messages
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Interview chat error: {e}")
            raise Exception(f"Interview coach unavailable: {str(e)}")

    def _fallback_questions(self, role: str, num: int) -> List[Dict]:
        base = [
            {"id": 1, "question": f"Tell me about yourself and why you're interested in the {role} role.",
             "type": "hr", "difficulty": "easy",
             "hints": "Give a 2-minute structured summary of your background.",
             "ideal_answer_points": ["Brief background", "Relevant skills", "Why this role"]},
            {"id": 2, "question": "Describe a challenging project you worked on and how you handled it.",
             "type": "behavioural", "difficulty": "medium",
             "hints": "Use the STAR method: Situation, Task, Action, Result.",
             "ideal_answer_points": ["Clear situation", "Specific actions taken", "Measurable outcome"]},
            {"id": 3, "question": f"What are the key technical skills required for a {role} and how do you rate yourself?",
             "type": "technical", "difficulty": "medium",
             "hints": "Be honest about your skill levels.",
             "ideal_answer_points": ["Identifies correct skills", "Honest self-assessment", "Shows growth mindset"]},
        ]
        return base[:num]


_interview_coach = None

def get_interview_coach() -> InterviewCoach:
    global _interview_coach
    if _interview_coach is None:
        _interview_coach = InterviewCoach()
    return _interview_coach