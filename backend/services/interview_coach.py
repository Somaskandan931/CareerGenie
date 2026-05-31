"""
backend/services/interview_coach.py
=====================================
AI Interview Coach service.
Conducts mock interviews, evaluates answers, and provides structured feedback.
Supports technical, behavioural, and HR interview modes.

Refactored to:
  - Route all LLM calls through ``backend.core.ai_pipeline``
  - Use centralized prompts from ``backend.core.prompts``
  - Sanitize user-supplied inputs
  - Use structured logging via ``backend.core.logging``
"""
from __future__ import annotations

from typing import Dict, List, Optional

from backend.core import ai_pipeline
from backend.core.config import settings
from backend.core.exceptions import LLMUnavailableError
from backend.core.logging import get_logger
from backend.core.prompts import Prompts

logger = get_logger("interview_coach")

_INTERVIEWER_SYSTEM = """You are a professional interviewer conducting a mock job interview.
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

    def generate_questions(
        self,
        role: str,
        interview_type: str = "mixed",
        resume_text: Optional[str] = None,
        num_questions: int = 10,
    ) -> List[Dict]:
        """
        Pre-generate a bank of interview questions for a role.
        """
        if interview_type == "hr":
            return self.generate_hr_questions(role, resume_text, None, None, num_questions)

        system, user = Prompts.interview_questions(
            role=role,
            interview_type=interview_type,
            num_questions=num_questions,
            resume_text=resume_text,
        )

        try:
            questions = ai_pipeline.call_json(
                system, user,
                temp=0.7,
                max_tokens=2000,
                smart=True,
            )
            if not isinstance(questions, list):
                return self._fallback_questions(role, num_questions)

            validated = []
            for i, q in enumerate(questions[:num_questions]):
                if isinstance(q, dict):
                    validated.append({
                        "id":                  q.get("id", i + 1),
                        "question":            q.get("question", f"Tell me about your experience with {role}"),
                        "type":                q.get("type", interview_type),
                        "difficulty":          q.get("difficulty", "medium"),
                        "hints":               q.get("hints", "Be specific and use examples"),
                        "ideal_answer_points": q.get("ideal_answer_points", ["Be concise", "Use STAR method"]),
                    })
            return validated or self._fallback_questions(role, num_questions)

        except Exception as exc:
            logger.error("Question generation error: %s", exc)
            return self._fallback_questions(role, num_questions)

    def generate_hr_questions(
        self,
        role: str,
        resume_text: Optional[str] = None,
        company_type: Optional[str] = None,
        focus_area: Optional[str] = None,
        num_questions: int = 8,
    ) -> List[Dict]:
        """Generate HR-specific interview questions."""
        system, user = Prompts.hr_panel(
            resume_text=resume_text or "",
            target_role=role,
            company_type=company_type or "mid-size",
            focus_area=focus_area or "general",
            num_questions=num_questions,
        )

        # hr_panel returns a full evaluation dict; for question-only mode
        # we use the interview_questions prompt with "hr" type instead
        system, user = Prompts.interview_questions(
            role=role,
            interview_type="hr",
            num_questions=num_questions,
            resume_text=resume_text,
        )

        try:
            questions = ai_pipeline.call_json(
                system, user,
                temp=0.7,
                max_tokens=2000,
                smart=True,
            )
            if not isinstance(questions, list):
                return self._fallback_hr_questions(role, num_questions)

            validated = []
            for i, q in enumerate(questions[:num_questions]):
                if isinstance(q, dict):
                    validated.append({
                        "id":               q.get("id", i + 1),
                        "category":         q.get("category", "general"),
                        "question":         q.get("question", f"Tell me about your experience with {role}"),
                        "difficulty":       q.get("difficulty", "medium"),
                        "hints":            q.get("hints", "Be specific and use examples from your experience"),
                        "what_to_look_for": q.get("what_to_look_for", ["Clear examples", "Relevant experience"]),
                        "follow_up":        q.get("follow_up", "Can you elaborate on that?"),
                    })
            return validated or self._fallback_hr_questions(role, num_questions)

        except Exception as exc:
            logger.error("HR questions generation error: %s", exc)
            return self._fallback_hr_questions(role, num_questions)

    def evaluate_answer(
        self,
        question: str,
        answer: str,
        role: str,
        interview_type: str = "mixed",
    ) -> Dict:
        """Evaluate a candidate's answer and return structured feedback."""
        safe_answer = ai_pipeline.sanitize_user_content(answer, max_length=2000)
        system, user = Prompts.evaluate_answer(
            question=question,
            answer=safe_answer,
            role=role,
            interview_type=interview_type,
        )

        try:
            result = ai_pipeline.call_json(system, user, temp=0.7, max_tokens=600)
            if isinstance(result, dict):
                return result
        except Exception as exc:
            logger.error("Answer evaluation error: %s", exc)

        return {
            "score": 5,
            "strengths": ["Attempted the question"],
            "improvements": ["Provide more specific examples", "Structure your answer using STAR method"],
            "sample_better_answer": "Unable to generate sample answer at this time.",
            "follow_up_question": "Can you elaborate on that point?",
        }

    def chat(
        self,
        messages: List[Dict],
        role: str,
        interview_type: str = "mixed",
        resume_text: Optional[str] = None,
    ) -> str:
        """Conduct a live mock interview via back-and-forth chat."""
        system = _INTERVIEWER_SYSTEM
        system += f"\n\nRole being interviewed for: {role}"
        system += f"\nInterview type: {interview_type}"
        if resume_text:
            safe_resume = ai_pipeline.sanitize_user_content(resume_text, max_length=800)
            system += f"\nCandidate's background: {safe_resume}"

        if not any(m["role"] == "assistant" for m in messages):
            system += "\n\nStart with a brief welcome, explain the format, then ask your first question."

        try:
            return ai_pipeline.call(
                system=system,
                user=messages[-1]["content"] if messages else "Start the interview",
                temp=0.7,
                max_tokens=settings.MAX_TOKENS_CHAT,
                use_cache=False,
            )
        except LLMUnavailableError as exc:
            logger.error("Interview chat LLM unavailable: %s", exc)
            raise Exception(f"Interview coach unavailable: {exc}")
        except Exception as exc:
            logger.error("Interview chat error: %s", exc)
            raise Exception(f"Interview coach unavailable: {exc}")

    # ── Fallbacks ─────────────────────────────────────────────────────────────

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
             "ideal_answer_points": ["Identifies correct skills", "Honest self-assessment", "Growth mindset"]},
        ]
        return base[:num]

    def _fallback_hr_questions(self, role: str, num_questions: int) -> List[Dict]:
        hr_questions = [
            {"id": 1, "category": "motivation",
             "question": f"Tell me about yourself and why you're interested in this {role} role.",
             "difficulty": "easy", "hints": "Focus on your relevant experience and passion.",
             "what_to_look_for": ["Clear career narrative", "Specific interest", "Enthusiasm"],
             "follow_up": "What specific skills make you a good fit?"},
            {"id": 2, "category": "cultural_fit",
             "question": "Describe your ideal work environment.",
             "difficulty": "easy", "hints": "Think about environments you've thrived in.",
             "what_to_look_for": ["Self-awareness", "Realistic expectations"],
             "follow_up": "How would you handle a disagreement with a colleague?"},
            {"id": 3, "category": "teamwork",
             "question": "Tell me about a time you worked successfully in a team.",
             "difficulty": "medium", "hints": "Use the STAR method.",
             "what_to_look_for": ["Clear example", "Specific contribution", "Positive outcome"],
             "follow_up": "What role did you play?"},
            {"id": 4, "category": "problem_solving",
             "question": "Describe a challenging situation at work and how you resolved it.",
             "difficulty": "medium", "hints": "Focus on problem, actions, result.",
             "what_to_look_for": ["Problem identification", "Action taken", "Measurable result"],
             "follow_up": "What did you learn?"},
            {"id": 5, "category": "career_goals",
             "question": "Where do you see yourself in 3-5 years?",
             "difficulty": "medium", "hints": "Be realistic but ambitious.",
             "what_to_look_for": ["Career progression clarity", "Alignment with role"],
             "follow_up": "How does this role fit those plans?"},
            {"id": 6, "category": "communication",
             "question": "How do you handle feedback and constructive criticism?",
             "difficulty": "easy", "hints": "Show openness to growth.",
             "what_to_look_for": ["Openness to feedback", "Learning attitude"],
             "follow_up": "Tell me about a time you received difficult feedback."},
            {"id": 7, "category": "leadership",
             "question": "Describe a time you took initiative without being asked.",
             "difficulty": "medium", "hints": "Think about going above and beyond.",
             "what_to_look_for": ["Proactive behavior", "Impact", "Self-motivation"],
             "follow_up": "What was the outcome?"},
            {"id": 8, "category": "work_ethic",
             "question": "How do you prioritize and manage multiple deadlines?",
             "difficulty": "easy", "hints": "Share your actual system or method.",
             "what_to_look_for": ["Organization skills", "Time management"],
             "follow_up": "What tools or methods do you use?"},
        ]
        return hr_questions[:num_questions]


# ── Singleton ──────────────────────────────────────────────────────────────────

_interview_coach: Optional[InterviewCoach] = None


def get_interview_coach() -> InterviewCoach:
    global _interview_coach
    if _interview_coach is None:
        _interview_coach = InterviewCoach()
    return _interview_coach
