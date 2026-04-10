"""
AI Interview Coach service.
Conducts mock interviews, evaluates answers, and provides structured feedback.
Supports technical, behavioural, and HR interview modes.
"""
from typing import List, Dict, Optional
import logging
import json
import re

from backend.config import settings
from backend.services.llm import llm_call_sync, llm_call_smart_sync


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
        pass

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
        # For HR interviews, use the dedicated HR method
        if interview_type == "hr":
            return self.generate_hr_questions(role, resume_text, None, None, num_questions)

        # For other types, use the original logic
        prompt = f"""Generate {num_questions} interview questions for a "{role}" position.
Interview type: {interview_type}
{'Candidate background: ' + resume_text[:600] if resume_text else ''}

Return ONLY a valid JSON array with this exact structure:
[
  {{
    "id": 1,
    "question": "<the interview question>",
    "type": "{interview_type}",
    "difficulty": "easy|medium|hard",
    "hints": "<1 sentence hint>",
    "ideal_answer_points": ["point1", "point2", "point3"]
  }}
]

Make questions specific to the role. No duplicates. Return ONLY valid JSON."""

        try:
            raw = llm_call_smart_sync(
                system="You are an expert interviewer. Respond with valid JSON only.",
                user=prompt,
                temp=0.7,
                max_tokens=2000,
            )

            raw = self._clean_json_response(raw)
            questions = json.loads(raw)

            validated_questions = []
            for i, q in enumerate(questions[:num_questions]):
                if isinstance(q, dict):
                    validated_questions.append({
                        "id": q.get("id", i + 1),
                        "question": q.get("question", f"Tell me about your experience with {role}"),
                        "type": q.get("type", interview_type),
                        "difficulty": q.get("difficulty", "medium"),
                        "hints": q.get("hints", "Be specific and use examples"),
                        "ideal_answer_points": q.get("ideal_answer_points", ["Be concise", "Use STAR method"])
                    })

            return validated_questions if validated_questions else self._fallback_questions(role, num_questions)

        except Exception as e:
            logger.error(f"Question generation error: {e}")
            return self._fallback_questions(role, num_questions)

    def generate_hr_questions(self, role: str, resume_text: Optional[str] = None,
                               company_type: Optional[str] = None,
                               focus_area: Optional[str] = None,
                               num_questions: int = 8) -> List[Dict]:
        """
        Generate HR-specific interview questions based on resume and role.

        Args:
            role: Target job role
            resume_text: Candidate's resume for personalized questions
            company_type: Type of company (startup, corporate, etc.)
            focus_area: Specific area to focus on (leadership, teamwork, etc.)
            num_questions: Number of questions to generate

        Returns:
            List of HR question dicts
        """
        # Build context from resume
        resume_context = ""
        if resume_text:
            # Extract key information from resume
            lines = resume_text[:1000].split('\n')
            recent_experience = ""
            skills = ""

            for line in lines[:20]:
                line_lower = line.lower()
                if 'experience' in line_lower or 'work' in line_lower:
                    recent_experience = line
                if 'skill' in line_lower:
                    skills = line

            resume_context = f"""
Candidate Background:
- Recent experience: {recent_experience[:200]}
- Key skills: {skills[:200]}
"""

        company_context = ""
        if company_type:
            company_context = f"\nCompany Type: {company_type}"

        focus_context = ""
        if focus_area:
            focus_context = f"\nFocus Area: {focus_area}"

        prompt = f"""You are an experienced HR interviewer. Generate {num_questions} HR interview questions for a "{role}" position.

{resume_context}
{company_context}
{focus_context}

HR questions should assess:
1. Cultural fit and values alignment
2. Motivation and career goals
3. Communication and teamwork
4. Problem-solving and conflict resolution
5. Leadership potential and initiative
6. Work ethic and reliability
7. Adaptability and learning ability
8. Salary expectations and career progression

Return ONLY a valid JSON array with this exact structure (no markdown, no extra text):
[
  {{
    "id": 1,
    "category": "motivation",
    "question": "Tell me about yourself and why you're interested in this {role} role.",
    "difficulty": "easy",
    "hints": "Focus on your relevant experience and passion for the role.",
    "what_to_look_for": ["Clear career narrative", "Specific interest in the role", "Enthusiasm"],
    "follow_up": "What specific skills make you a good fit for this position?"
  }}
]

Categories: motivation, cultural_fit, teamwork, problem_solving, leadership, career_goals, communication, work_ethic

Make questions specific to the {role} position and personalized to the candidate's resume when possible. No duplicates."""

        try:
            raw = llm_call_smart_sync(
                system="You are an expert HR interviewer. Respond with valid JSON only. No markdown, no explanations.",
                user=prompt,
                temp=0.7,
                max_tokens=2000,
            )

            # Clean and parse JSON
            raw = self._clean_json_response(raw)
            questions = json.loads(raw)

            # Validate and format questions
            validated_questions = []
            for i, q in enumerate(questions[:num_questions]):
                if isinstance(q, dict):
                    validated_questions.append({
                        "id": q.get("id", i + 1),
                        "category": q.get("category", "general"),
                        "question": q.get("question", f"Tell me about your experience with {role}"),
                        "difficulty": q.get("difficulty", "medium"),
                        "hints": q.get("hints", "Be specific and use examples from your experience"),
                        "what_to_look_for": q.get("what_to_look_for", ["Clear examples", "Relevant experience", "Positive attitude"]),
                        "follow_up": q.get("follow_up", "Can you elaborate on that?")
                    })

            if validated_questions:
                return validated_questions

            return self._fallback_hr_questions(role, num_questions)

        except json.JSONDecodeError as e:
            logger.error(f"HR questions JSON parse error: {e}")
            return self._fallback_hr_questions(role, num_questions)
        except Exception as e:
            logger.error(f"HR questions generation error: {e}")
            return self._fallback_hr_questions(role, num_questions)

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
            raw = llm_call_sync(
                system="You are an expert AI assistant. Respond clearly and concisely.",
                user=prompt,
                temp=0.7,
                max_tokens=600,
            )
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
            return llm_call_sync(
                system=system,
                user=messages[-1]["content"] if messages else "Start the interview",
                temp=0.7,
                max_tokens=settings.MAX_TOKENS_CHAT,
            )
        except Exception as e:
            logger.error(f"Interview chat error: {e}")
            raise Exception(f"Interview coach unavailable: {str(e)}")

    def _clean_json_response(self, raw: str) -> str:
        """Clean JSON response from LLM."""
        if not raw:
            return "[]"

        # Remove markdown code blocks
        raw = re.sub(r'```json\s*', '', raw)
        raw = re.sub(r'```\s*', '', raw)

        # Find JSON array
        start = raw.find('[')
        end = raw.rfind(']') + 1

        if start >= 0 and end > start:
            raw = raw[start:end]
        else:
            return "[]"

        # Remove trailing commas
        raw = re.sub(r',\s*}', '}', raw)
        raw = re.sub(r',\s*]', ']', raw)

        return raw.strip()

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

    def _fallback_hr_questions(self, role: str, num_questions: int) -> List[Dict]:
        """Fallback HR questions when generation fails."""
        hr_questions = [
            {
                "id": 1,
                "category": "motivation",
                "question": f"Tell me about yourself and why you're interested in this {role} role.",
                "difficulty": "easy",
                "hints": "Focus on your relevant experience and passion for the role.",
                "what_to_look_for": ["Clear career narrative", "Specific interest in the role", "Enthusiasm"],
                "follow_up": "What specific skills make you a good fit for this position?"
            },
            {
                "id": 2,
                "category": "cultural_fit",
                "question": "Describe your ideal work environment and company culture.",
                "difficulty": "easy",
                "hints": "Think about what environments you've thrived in before.",
                "what_to_look_for": ["Alignment with company values", "Self-awareness", "Realistic expectations"],
                "follow_up": "How would you handle a disagreement with a colleague?"
            },
            {
                "id": 3,
                "category": "teamwork",
                "question": "Tell me about a time you worked successfully in a team.",
                "difficulty": "medium",
                "hints": "Use the STAR method: Situation, Task, Action, Result.",
                "what_to_look_for": ["Clear example", "Specific contribution", "Positive outcome"],
                "follow_up": "What role did you play in that team?"
            },
            {
                "id": 4,
                "category": "problem_solving",
                "question": "Describe a challenging situation at work and how you resolved it.",
                "difficulty": "medium",
                "hints": "Focus on the problem, your actions, and the result.",
                "what_to_look_for": ["Problem identification", "Action taken", "Measurable result"],
                "follow_up": "What did you learn from that experience?"
            },
            {
                "id": 5,
                "category": "career_goals",
                "question": "Where do you see yourself in 3-5 years?",
                "difficulty": "medium",
                "hints": "Be realistic but ambitious.",
                "what_to_look_for": ["Career progression clarity", "Alignment with role", "Growth mindset"],
                "follow_up": "How does this role fit into those plans?"
            },
            {
                "id": 6,
                "category": "communication",
                "question": "How do you handle feedback and constructive criticism?",
                "difficulty": "easy",
                "hints": "Show that you're open to growth.",
                "what_to_look_for": ["Openness to feedback", "Learning attitude", "Professional maturity"],
                "follow_up": "Tell me about a time you received difficult feedback."
            },
            {
                "id": 7,
                "category": "leadership",
                "question": "Describe a time you took initiative without being asked.",
                "difficulty": "medium",
                "hints": "Think about times you went above and beyond.",
                "what_to_look_for": ["Proactive behavior", "Impact of actions", "Self-motivation"],
                "follow_up": "What was the outcome of your initiative?"
            },
            {
                "id": 8,
                "category": "work_ethic",
                "question": "How do you prioritize and manage multiple deadlines?",
                "difficulty": "easy",
                "hints": "Share your actual system or method.",
                "what_to_look_for": ["Organization skills", "Time management", "Reliability"],
                "follow_up": "What tools or methods do you use?"
            }
        ]

        return hr_questions[:num_questions]


# Singleton
_interview_coach = None

def get_interview_coach() -> InterviewCoach:
    global _interview_coach
    if _interview_coach is None:
        _interview_coach = InterviewCoach()
    return _interview_coach