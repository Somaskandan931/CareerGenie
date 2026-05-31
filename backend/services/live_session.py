"""
Live Interview Session - Stub implementation.
"""
from typing import Dict


class InterviewEngine:
    def start_session(self, session_id: str, role: str, interview_type: str = "mixed",
                      resume_text: str = "", num_questions: int = 10) -> Dict:
        return {
            "session_id": session_id,
            "status": "started",
            "role": role,
            "interview_type": interview_type,
            "message": "Live interview session started. Use /interview/live/next to continue.",
            "first_question": f"Welcome to your {role} interview! Tell me about yourself.",
        }

    def next_question(self, session_id: str, transcript: str) -> Dict:
        return {
            "session_id": session_id,
            "status": "continuing",
            "message": "Live session processing. Please implement full session management.",
            "next_question": "Can you describe a challenging project you have worked on?",
        }


interview_engine = InterviewEngine()
