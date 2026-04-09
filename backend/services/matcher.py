"""
matcher.py  (UPGRADED)
======================
Changes from brutal evaluation:
  ✅ Static 35/45/20 weights → adaptive per-user weights via FeedbackEngine
  ✅ Stores per-component scores (semantic_score, skills_score, title_score)
     so FeedbackEngine can do meaningful gradient updates
  ✅ Calls personalise_score() for users with feedback history
  ✅ Cold-start handled transparently (falls back to prior weights)
  ✅ component_contributions dict attached to each match for the feedback
     recording endpoint to persist
  ✅ Uses llm.py waterfall (Groq → Anthropic → Gemini) — no direct SDK calls
"""
from typing import List, Dict, Optional
import logging
import re
from datetime import datetime

from backend.config import settings
from backend.services.llm import llm_call_sync
from backend.services.vector_store import vector_store

logger = logging.getLogger(__name__)


class JobMatcher:
    def __init__(self):
        self.skill_patterns = [
            r'\b(python|java|javascript|typescript|c\+\+|c#|ruby|go|rust|php|swift|kotlin)\b',
            r'\b(react|angular|vue|django|flask|fastapi|spring|express|node\.?js)\b',
            r'\b(sql|mysql|postgresql|mongodb|redis|dynamodb|oracle)\b',
            r'\b(aws|azure|gcp|docker|kubernetes|jenkins|terraform|ansible)\b',
            r'\b(machine learning|deep learning|tensorflow|pytorch|scikit-learn|nlp|computer vision)\b',
            r'\b(git|jira|confluence|linux|agile|scrum)\b',
        ]
        self.critical_skills = [
            "python", "java", "javascript", "sql", "aws", "react", "docker",
        ]

    # ── Public API ─────────────────────────────────────────────────────────────

    def match_resume_to_jobs(
        self,
        resume_text: str,
        top_k: int = 10,
        force_refresh: bool = False,
        location: str = "India",
        user_id: Optional[str] = None,   # NEW — enables personalised ranking
    ) -> List[Dict]:
        logger.info(f"Matching resume to top {top_k} jobs (user_id={user_id})")

        # Optionally refresh job index
        if force_refresh or vector_store.get_stats()["total_jobs"] < 20:
            self._refresh_jobs(resume_text, location, force_refresh)

        retrieved_jobs = vector_store.search(resume_text, top_k=top_k * 2)
        if not retrieved_jobs:
            logger.warning("No jobs found in vector store")
            return []

        resume_skills = self._extract_skills(resume_text)
        logger.info(f"Extracted {len(resume_skills)} skills from resume")

        # Load adaptive weights (falls back to prior for cold-start users)
        adaptive_weights = self._get_weights(user_id)

        matches = []
        for job in retrieved_jobs:
            job_skills = self._extract_skills(job["description"])
            matched    = list(set(resume_skills) & set(job_skills))
            missing    = list(set(job_skills)   - set(resume_skills))

            # ── Compute raw component scores (0-100) ──────────────────────────
            sem_raw   = max(0.0, 100.0 * (1 - min(job.get("distance", 0.5), 1.0)))
            skill_raw = self._skills_raw(matched, missing)
            title_raw = self._calculate_title_match(resume_text, job["title"])
            # title_raw is already 0-20; normalise to 0-100 for uniform weighting
            title_raw_norm = title_raw * 5.0

            # ── Weighted sum with adaptive weights ────────────────────────────
            base_score = (
                adaptive_weights["semantic"] * sem_raw
                + adaptive_weights["skills"]   * skill_raw
                + adaptive_weights["title"]    * title_raw_norm
            )

            # Critical skill penalty
            critical_missing = [s for s in missing if s.lower() in self.critical_skills]
            penalty = min(15, len(critical_missing) * 5)
            base_score = max(0.0, min(100.0, base_score - penalty))

            if base_score < 30:
                continue

            # ── Personalisation layer ─────────────────────────────────────────
            final_score = base_score
            if user_id:
                try:
                    from backend.services.feedback_engine import get_feedback_engine
                    engine = get_feedback_engine()
                    final_score = engine.personalise_score(
                        user_id,
                        job,
                        {
                            "semantic": sem_raw,
                            "skills":   skill_raw,
                            "title":    title_raw_norm,
                        },
                    )
                except Exception as e:
                    logger.warning(f"Personalisation skipped: {e}")

            # LLM explanation for strong matches
            explanation = ""
            if final_score > 50:
                explanation = self._generate_explanation(
                    resume_text, job["title"], job["company"],
                    job["description"], matched, missing,
                )

            matches.append({
                "job_id":       job["id"],
                "title":        job["title"],
                "company":      job["company"],
                "location":     job["location"],
                "match_score":  round(final_score, 1),
                # ── per-component scores (NEW — needed by FeedbackEngine) ──
                "semantic_score": round(sem_raw,        1),
                "skills_score":   round(skill_raw,      1),
                "title_score":    round(title_raw_norm, 1),
                # ── contribution fractions (used for weight gradient update) ─
                "component_contributions": {
                    "semantic": adaptive_weights["semantic"],
                    "skills":   adaptive_weights["skills"],
                    "title":    adaptive_weights["title"],
                },
                "matched_skills":    matched[:8],
                "missing_skills":    missing[:5],
                "explanation":       explanation,
                "recommendation":    self._get_recommendation(final_score),
                "apply_link":        job.get("apply_link", ""),
                "fetched_at":        job.get("fetched_at", datetime.now().isoformat()),
                "personalised":      user_id is not None,
            })

        matches.sort(key=lambda x: x["match_score"], reverse=True)
        logger.info(f"Generated {len(matches[:top_k])} job matches")
        return matches[:top_k]

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _get_weights(self, user_id: Optional[str]) -> Dict[str, float]:
        """Return adaptive weights for user or population prior."""
        if not user_id:
            return {"semantic": 0.35, "skills": 0.45, "title": 0.20}
        try:
            from backend.services.feedback_engine import get_feedback_engine
            return get_feedback_engine().get_weights(user_id)
        except Exception:
            return {"semantic": 0.35, "skills": 0.45, "title": 0.20}

    def _refresh_jobs(self, resume_text: str, location: str, force: bool) -> None:
        try:
            from backend.services.job_scraper import get_job_scraper
            scraper    = get_job_scraper()
            target_role = self._extract_target_role(resume_text)
            fresh_jobs  = scraper.fetch_jobs(query=target_role, location=location, num_jobs=50)
            if fresh_jobs:
                if force:
                    vector_store.clear()
                vector_store.index_jobs(fresh_jobs)
                logger.info(f"Refreshed with {len(fresh_jobs)} fresh jobs")
        except Exception as e:
            logger.error(f"Failed to refresh jobs: {e}")

    def _skills_raw(self, matched: List[str], missing: List[str]) -> float:
        total = len(matched) + len(missing)
        if total == 0:
            return 50.0
        return 100.0 * len(matched) / total

    def _extract_target_role(self, resume_text: str) -> str:
        common_roles = [
            "software engineer", "data scientist", "machine learning engineer",
            "web developer", "devops engineer", "product manager", "data analyst",
            "frontend developer", "backend developer", "full stack developer",
            "cloud engineer", "site reliability engineer",
        ]
        text_lower = resume_text.lower()
        for role in common_roles:
            if role in text_lower:
                return role
        return "software engineer"

    def _extract_skills(self, text: str) -> List[str]:
        text_lower = text.lower()
        skills: set = set()
        for pattern in self.skill_patterns:
            for match in re.findall(pattern, text_lower, re.IGNORECASE):
                if isinstance(match, tuple):
                    skills.update(m for m in match if m)
                else:
                    skills.add(match.lower())
        return sorted(skills)

    def _calculate_title_match(self, resume_text: str, job_title: str) -> float:
        resume_lower = resume_text.lower()
        title_lower  = job_title.lower()
        title_words  = set(re.findall(r'\b[a-z]+\b', title_lower))

        variations = {
            "engineer":  ["engineer", "developer", "programmer", "architect"],
            "developer": ["developer", "engineer", "programmer", "coder"],
            "senior":    ["senior", "lead", "principal", "staff"],
            "junior":    ["junior", "entry", "fresher", "graduate"],
            "data":      ["data", "analytics", "analyst", "scientist"],
            "cloud":     ["cloud", "aws", "azure", "gcp"],
            "frontend":  ["frontend", "front-end", "ui", "react", "vue", "angular"],
            "backend":   ["backend", "back-end", "api", "server"],
            "fullstack": ["fullstack", "full-stack", "full stack"],
        }

        score = 0
        matched_terms: set = set()
        for word in title_words:
            if word in resume_lower:
                score += 4
                matched_terms.add(word)
            elif word in variations:
                for variant in variations[word]:
                    if variant in resume_lower and variant not in matched_terms:
                        score += 2
                        matched_terms.add(variant)
                        break
        return min(20.0, float(score))

    def _get_recommendation(self, score: float) -> str:
        if score >= 80:  return "Excellent Match"
        if score >= 65:  return "Strong Match"
        if score >= 50:  return "Good Match"
        if score >= 35:  return "Moderate Match"
        return "Weak Match"

    def _generate_explanation(
        self,
        resume_text: str,
        job_title: str,
        job_company: str,
        job_description: str,
        matched_skills: List[str],
        missing_skills: List[str],
    ) -> str:
        prompt = f"""You are an expert career advisor analysing a job match.
Resume: {resume_text[:1200]}
Job: {job_title} at {job_company}
Description: {job_description[:1000]}
Matched Skills: {', '.join(matched_skills) if matched_skills else 'None'}
Missing Skills: {', '.join(missing_skills[:3]) if missing_skills else 'None'}

Write 2-3 sentences: what makes this a good/weak match, one gap to address, final action."""

        try:
            return llm_call_sync(
                system="You are an expert career advisor.",
                user=prompt,
                temp=0.7,
                max_tokens=150,
            )
        except Exception as e:
            logger.error(f"Explanation error: {e}")
            return (
                f"Good match on {len(matched_skills)} skills. "
                + (f"Focus on {missing_skills[0]}." if missing_skills else "Ready to apply!")
            )


# ── Singleton ──────────────────────────────────────────────────────────────────
_job_matcher: Optional[JobMatcher] = None


def get_job_matcher() -> JobMatcher:
    global _job_matcher
    if _job_matcher is None:
        _job_matcher = JobMatcher()
    return _job_matcher