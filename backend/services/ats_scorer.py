from groq import Groq
from typing import List, Dict, Optional
import logging
import json
import re

from backend.config import settings

logger = logging.getLogger(__name__)


class ATSScorer:
    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not configured")
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        logger.info("ATSScorer initialized with Groq")

    def score_resume(self, resume_text: str, target_role: str = "Software Engineer") -> Dict:
        """
        Analyse a resume and return a structured ATS-style evaluation.
        Returns strict JSON matching the ATSScoreResult schema.
        """
        prompt = f"""You are an expert ATS (Applicant Tracking System) analyzer and resume coach.

Analyze the following resume for the target role: "{target_role}"

RESUME:
{resume_text[:3000]}

Return ONLY a valid JSON object with EXACTLY this structure (no markdown, no extra text):
{{
  "overall_score": <integer 0-100>,
  "keyword_score": <integer 0-100>,
  "format_score": <integer 0-100>,
  "missing_keywords": [<list of 5-8 important missing keywords for {target_role}>],
  "found_keywords": [<list of relevant keywords found in the resume>],
  "section_feedback": {{
    "experience": "<2-3 sentences of specific feedback on experience section>",
    "skills": "<2-3 sentences of specific feedback on skills section>",
    "education": "<1-2 sentences of specific feedback on education section>",
    "summary": "<1-2 sentences on the professional summary/objective, or 'No summary found - add one'>",
    "formatting": "<1-2 sentences on ATS formatting issues>"
  }},
  "bullet_quality": {{
    "score": <integer 0-100>,
    "issues": [<list of 2-4 specific bullet point issues found>],
    "good_examples": [<list of 1-2 strong bullet points from the resume, or empty list>]
  }},
  "improvements": [<list of exactly 6 specific, actionable improvement suggestions>],
  "ats_verdict": "<one of: Excellent | Good | Needs Work | Poor>",
  "verdict_reason": "<1 sentence explaining the verdict>"
}}

Scoring guide:
- overall_score: weighted average considering all factors
- keyword_score: how well resume keywords match {target_role} job requirements
- format_score: ATS-friendliness (no tables, no columns, proper headers, standard fonts)

Be specific, actionable, and honest. Reference actual content from the resume."""

        try:
            response = self.client.chat.completions.create(
                model=settings.GROQ_SMART_MODEL,
                max_tokens=settings.MAX_TOKENS_CAREER_ADVICE,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            raw = response.choices[0].message.content.strip()
            # Strip markdown fences if present
            raw = re.sub(r"^```json\s*", "", raw)
            raw = re.sub(r"^```\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            result = json.loads(raw)
            return self._validate_result(result, target_role)
        except json.JSONDecodeError as e:
            logger.error(f"ATS score JSON parse error: {e}\nRaw: {raw[:300]}")
            return self._fallback_result(resume_text, target_role)
        except Exception as e:
            logger.error(f"ATS score error: {e}")
            return self._fallback_result(resume_text, target_role)

    def _validate_result(self, result: Dict, target_role: str) -> Dict:
        """Ensure all required fields exist with correct types."""
        defaults = {
            "overall_score": 50,
            "keyword_score": 50,
            "format_score": 60,
            "missing_keywords": [],
            "found_keywords": [],
            "section_feedback": {
                "experience": "Review your experience section.",
                "skills": "Ensure skills match the target role.",
                "education": "Education section looks adequate.",
                "summary": "Consider adding a professional summary.",
                "formatting": "Check ATS compatibility.",
            },
            "bullet_quality": {"score": 50, "issues": [], "good_examples": []},
            "improvements": ["Tailor resume to job description"],
            "ats_verdict": "Needs Work",
            "verdict_reason": "Resume requires optimization for ATS systems.",
        }
        for key, val in defaults.items():
            if key not in result:
                result[key] = val
        # Clamp scores
        for score_key in ("overall_score", "keyword_score", "format_score"):
            result[score_key] = max(0, min(100, int(result.get(score_key, 50))))
        if "score" in result.get("bullet_quality", {}):
            result["bullet_quality"]["score"] = max(0, min(100, int(result["bullet_quality"]["score"])))
        return result

    def _fallback_result(self, resume_text: str, target_role: str) -> Dict:
        word_count = len(resume_text.split())
        score = min(60, max(20, word_count // 5))
        return {
            "overall_score": score,
            "keyword_score": score - 10,
            "format_score": 55,
            "missing_keywords": ["quantified achievements", "action verbs", "technical skills", "certifications", "leadership", "metrics"],
            "found_keywords": [],
            "section_feedback": {
                "experience": "Unable to fully analyze. Ensure experience is clearly formatted with bullet points.",
                "skills": "Add a dedicated skills section with relevant technical and soft skills.",
                "education": "Include degree, institution, and graduation year.",
                "summary": "Add a 2-3 sentence professional summary at the top.",
                "formatting": "Use standard section headers and avoid tables/columns for ATS compatibility.",
            },
            "bullet_quality": {
                "score": 40,
                "issues": ["Missing quantified metrics", "Weak action verbs", "Too vague — be more specific"],
                "good_examples": [],
            },
            "improvements": [
                "Add quantified achievements (e.g., 'Increased sales by 30%')",
                "Use strong action verbs (Led, Built, Optimized, Delivered)",
                f"Add role-specific keywords for {target_role}",
                "Include a professional summary section",
                "Ensure consistent date formatting throughout",
                "Remove tables and columns for better ATS parsing",
            ],
            "ats_verdict": "Needs Work",
            "verdict_reason": "Resume needs keyword optimization and stronger impact statements.",
        }


try:
    ats_scorer = ATSScorer()
except Exception as e:
    logger.error(f"Failed to initialize ATSScorer: {e}")
    ats_scorer = None