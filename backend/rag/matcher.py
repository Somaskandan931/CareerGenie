from typing import List, Dict, Any
import os
import logging
import anthropic
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class RAGJobMatcher:
    """
    Resume ↔ Job matcher
    - Skill overlap
    - Semantic similarity
    - Optional LLM explanation
    """

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else None

        if not self.client:
            logger.warning("⚠️  Anthropic not configured — using rule-based explanations")

    # ------------------------------------------------------------------
    # Skill extraction & scoring
    # ------------------------------------------------------------------

    def _extract_resume_skills(self, resume_text: str) -> List[str]:
        skills = [
            "python", "java", "javascript", "react", "node",
            "sql", "aws", "docker", "machine learning", "ai",
            "tensorflow", "pytorch", "django", "spring"
        ]
        text = resume_text.lower()
        return [s for s in skills if s in text]

    def _skill_match_score(
        self,
        resume_skills: List[str],
        job_skills: List[str]
    ) -> float:
        if not job_skills:
            return 0.0

        r = set(s.lower() for s in resume_skills)
        j = set(s.lower() for s in job_skills)

        return (len(r & j) / len(j)) * 100

    # ------------------------------------------------------------------
    # Explanation generation
    # ------------------------------------------------------------------

    def _fallback_explanation(
        self,
        matched: List[str],
        missing: List[str],
        score: float
    ) -> str:
        if score >= 75:
            base = "Strong match for this role."
        elif score >= 55:
            base = "Moderate match with some gaps."
        else:
            base = "Low match based on current skills."

        if matched:
            base += f" Matching skills: {', '.join(matched[:4])}."
        if missing:
            base += f" Missing skills: {', '.join(missing[:3])}."

        return base

    def _llm_explanation(
        self,
        resume_text: str,
        job: Dict[str, Any],
        matched: List[str],
        missing: List[str]
    ) -> str:
        prompt = f"""
Analyze the resume-job fit briefly.

JOB: {job['title']} at {job['company']}
SKILLS REQUIRED: {', '.join(job['skills_required'])}

MATCHED SKILLS: {', '.join(matched) or 'None'}
MISSING SKILLS: {', '.join(missing) or 'None'}

Provide a concise 2-sentence explanation.
"""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=120,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()

    def _recommendation(self, score: float) -> str:
        if score >= 75:
            return "Highly Recommended"
        if score >= 60:
            return "Recommended"
        if score >= 45:
            return "Consider"
        return "Not Recommended"

    # ------------------------------------------------------------------
    # MAIN ENTRY POINT
    # ------------------------------------------------------------------

    def match_jobs(
        self,
        resume_text: str,
        retrieved_jobs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:

        resume_skills = self._extract_resume_skills(resume_text)
        results = []

        for job in retrieved_jobs:
            skill_score = self._skill_match_score(
                resume_skills,
                job.get("skills_required", [])
            )

            semantic_score = job.get("similarity_score", 0)
            final_score = round((0.6 * skill_score) + (0.4 * semantic_score), 2)

            matched = [
                s for s in job.get("skills_required", [])
                if s.lower() in (x.lower() for x in resume_skills)
            ]

            missing = [
                s for s in job.get("skills_required", [])
                if s.lower() not in (x.lower() for x in resume_skills)
            ]

            # Explanation
            if self.client and final_score >= 60:
                try:
                    explanation = self._llm_explanation(
                        resume_text, job, matched, missing
                    )
                except Exception as e:
                    logger.debug(f"LLM failed: {e}")
                    explanation = self._fallback_explanation(
                        matched, missing, final_score
                    )
            else:
                explanation = self._fallback_explanation(
                    matched, missing, final_score
                )

            # 🔑 FRONTEND-READY OBJECT (NO NESTING)
            results.append({
                "job_id": job["job_id"],
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "employment_type": job.get("employment_type", "Full-time"),
                "salary_range": job.get("salary_range", "Not specified"),
                "apply_link": job.get("apply_link", ""),
                "match_score": final_score,
                "similarity_score": semantic_score,
                "matched_skills": matched,
                "missing_required_skills": missing,
                "explanation": explanation,
                "recommendation": self._recommendation(final_score)
            })

        # Sort best matches first
        return sorted(results, key=lambda x: x["match_score"], reverse=True)
