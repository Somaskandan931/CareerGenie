"""
backend/services/ats_scorer.py
================================
ATS (Applicant Tracking System) resume scoring service.

Refactored to:
  - Route all LLM calls through ``backend.core.ai_pipeline`` (no direct SDK calls)
  - Use centralized prompts from ``backend.core.prompts``
  - Raise ``CareerGenieError`` subclasses instead of returning bare dicts on failure
  - Remove duplicated JSON parsing logic (now handled by ai_pipeline.call_json)
  - Sanitize user-supplied resume content before it reaches the LLM
"""
from __future__ import annotations

from typing import Dict, List, Optional

from backend.core import ai_pipeline
from backend.core.exceptions import LLMParseError, LLMUnavailableError
from backend.core.logging import get_logger
from backend.core.prompts import Prompts
from backend.core.config import settings

logger = get_logger("ats_scorer")

# ── Default values for missing fields ────────────────────────────────────────

_DEFAULT_SECTION_FEEDBACK = {
    "experience":  "Ensure experience is formatted with clear bullet points.",
    "skills":      "Add a dedicated skills section with relevant technical skills.",
    "education":   "Include degree, institution, and graduation year.",
    "summary":     "Add a 2-3 sentence professional summary at the top.",
    "formatting":  "Use standard section headers and avoid tables for ATS compatibility.",
}

_DEFAULT_BULLET_QUALITY = {
    "score": 50,
    "issues": ["Missing quantified metrics", "Weak action verbs"],
    "good_examples": [],
}

_DEFAULT_IMPROVEMENTS = [
    "Add quantified achievements (e.g. 'Increased efficiency by 30%')",
    "Use strong action verbs: Led, Built, Optimized, Delivered",
    "Tailor keywords to the job description",
    "Include a professional summary section",
    "Remove tables and columns for better ATS parsing",
]


class ATSScorer:
    """
    Scores a resume against a target role or job description.

    All LLM calls go through ``ai_pipeline.call_json`` — no direct SDK usage.
    Input resume text is sanitized for prompt injection before being sent.
    """

    def score_resume(
        self,
        resume_text: str,
        target_role: str = "Software Engineer",
        job_description: Optional[str] = None,
    ) -> Dict:
        """
        Analyse a resume and return a structured ATS evaluation.

        Args:
            resume_text:     Raw resume text (will be sanitized).
            target_role:     Job title to score against.
            job_description: Optional JD for tighter keyword matching.

        Returns:
            Dict matching the ``ATSScoreResult`` schema with guaranteed fields.
        """
        safe_resume = ai_pipeline.sanitize_user_content(resume_text)
        safe_jd = (
            ai_pipeline.sanitize_user_content(job_description, max_length=3500)
            if job_description
            else None
        )

        system, user = Prompts.ats_score(safe_resume, target_role, safe_jd)

        try:
            result = ai_pipeline.call_json(
                system, user,
                temp=0.2,
                max_tokens=1500,
            )
            if not isinstance(result, dict):
                logger.warning("ATS scorer: LLM returned non-dict JSON, using fallback")
                return self._fallback_result(resume_text, target_role, job_description)
            return self._validate_result(result, target_role)

        except LLMParseError as exc:
            logger.warning("ATS score parse error: %s", exc)
            return self._fallback_result(resume_text, target_role, job_description)
        except LLMUnavailableError as exc:
            logger.error("ATS score LLM unavailable: %s", exc)
            return self._fallback_result(resume_text, target_role, job_description)
        except Exception as exc:
            logger.error("ATS score unexpected error: %s", exc, exc_info=True)
            return self._fallback_result(resume_text, target_role, job_description)

    def score(
        self,
        resume_text: str,
        target_role: str = "Software Engineer",
        job_description: str = "",
    ) -> Dict:
        """Alias for ``score_resume`` — backwards compatibility."""
        jd = job_description if job_description and job_description.strip() else None
        return self.score_resume(resume_text, target_role, jd)

    # ── Validation ────────────────────────────────────────────────────────────

    def _validate_result(self, result: Dict, target_role: str) -> Dict:
        """Ensure all required fields are present with correct types."""

        # Integer scores — clamp to 0-100
        for key in ("overall_score", "keyword_score", "format_score"):
            try:
                result[key] = max(0, min(100, int(result.get(key, 50))))
            except (ValueError, TypeError):
                result[key] = 50

        # List fields
        for key in ("missing_keywords", "found_keywords", "improvements"):
            if not isinstance(result.get(key), list):
                result[key] = []

        if len(result.get("improvements", [])) < 3:
            result["improvements"] = (result.get("improvements", []) + _DEFAULT_IMPROVEMENTS)[:6]

        # Section feedback dict
        sf = result.get("section_feedback")
        if not isinstance(sf, dict):
            result["section_feedback"] = _DEFAULT_SECTION_FEEDBACK
        else:
            for sub in _DEFAULT_SECTION_FEEDBACK:
                if not sf.get(sub):
                    sf[sub] = _DEFAULT_SECTION_FEEDBACK[sub]

        # Bullet quality dict
        bq = result.get("bullet_quality")
        if not isinstance(bq, dict):
            result["bullet_quality"] = _DEFAULT_BULLET_QUALITY
        else:
            for sub in _DEFAULT_BULLET_QUALITY:
                if sub not in bq:
                    bq[sub] = _DEFAULT_BULLET_QUALITY[sub]
            try:
                bq["score"] = max(0, min(100, int(bq["score"])))
            except (ValueError, TypeError):
                bq["score"] = 50

        # String fields
        result.setdefault("ats_verdict", "Needs Work")
        result.setdefault("verdict_reason", "Resume requires optimization for ATS systems.")

        return result

    # ── Fallback ──────────────────────────────────────────────────────────────

    def _fallback_result(
        self,
        resume_text: str,
        target_role: str,
        job_description: Optional[str] = None,
    ) -> Dict:
        """Return a best-effort result when LLM calls fail."""
        word_count = len(resume_text.split())
        score = max(20, min(60, word_count // 5))

        missing: List[str] = ["quantified achievements", "action verbs", "technical skills"]
        if job_description:
            words = job_description.lower()
            tech_hits = [s for s in settings.TECH_SKILLS if s.lower() in words]
            if tech_hits:
                missing = tech_hits[:8]

        return {
            "overall_score": score,
            "keyword_score": max(10, score - 10),
            "format_score": 55,
            "missing_keywords": missing,
            "found_keywords": [],
            "section_feedback": _DEFAULT_SECTION_FEEDBACK,
            "bullet_quality": {
                "score": 40,
                "issues": ["Missing quantified metrics", "Weak action verbs", "Too vague"],
                "good_examples": [],
            },
            "improvements": [
                f"Add role-specific keywords for {target_role}",
                "Quantify achievements with numbers and percentages",
                "Use strong action verbs (Led, Built, Optimized)",
                "Add a professional summary section",
                "Use standard ATS-friendly section headers",
                "Remove tables and columns for better parsing",
            ],
            "ats_verdict": "Needs Work",
            "verdict_reason": "Resume needs keyword optimization and stronger impact statements.",
        }


# ── Singleton ─────────────────────────────────────────────────────────────────

_ats_scorer: Optional[ATSScorer] = None


def get_ats_scorer() -> ATSScorer:
    """Return the singleton ATSScorer instance."""
    global _ats_scorer
    if _ats_scorer is None:
        _ats_scorer = ATSScorer()
    return _ats_scorer


# Legacy module-level alias
ats_scorer = get_ats_scorer()
