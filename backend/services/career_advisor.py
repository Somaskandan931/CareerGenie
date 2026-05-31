"""
backend/services/career_advisor.py
====================================
AI career advisor — synthesises resume, ATS, job-match, and market
signals into personalised, structured career advice.

Refactored to:
  - Route all LLM calls through ``backend.core.ai_pipeline``
  - Use centralized prompts from ``backend.core.prompts``
  - Sanitize user-supplied inputs before they reach the LLM
  - Use structured logging via ``backend.core.logging``
  - Raise ``CareerGenieError`` subclasses on fatal failures
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

from backend.core import ai_pipeline
from backend.core.config import settings
from backend.core.exceptions import LLMUnavailableError
from backend.core.logging import get_logger
from backend.core.prompts import Prompts

logger = get_logger("career_advisor")


class CareerAdvisor:
    """
    Generates structured career advice by combining:
      - Resume text (skill extraction)
      - ATS score (keyword gap context)
      - Job matches (market signal)
      - Market insights (demand / salary trends)
      - User profile / behaviour signals (personalisation)
    """

    def generate_career_advice(
        self,
        resume_text: str,
        target_role: Optional[str] = None,
        current_role: Optional[str] = None,
        job_matches: Optional[List[Dict]] = None,
        ats_score: Optional[Dict] = None,
        market_insights: Optional[Dict] = None,
        user_profile: Optional[Dict] = None,
    ) -> Dict:
        """
        Generate structured career advice from multi-signal context.

        Returns a dict with keys: current_assessment, skill_gaps,
        learning_path, career_progression, market_insights, action_plan,
        context_used.
        """
        safe_resume = ai_pipeline.sanitize_user_content(resume_text)
        role = target_role or "Software Engineer"

        current_skills = self._extract_skills(safe_resume)
        advice = self._generate_advice(
            safe_resume, current_role, role, current_skills,
            job_matches, ats_score, market_insights, user_profile,
        )

        return {
            "current_assessment": advice.get("assessment", ""),
            "skill_gaps":         advice.get("skill_gaps", []),
            "learning_path":      self._build_learning_path(advice.get("skill_gaps", [])),
            "career_progression": self._career_stages(),
            "market_insights":    advice.get("market_insights", ""),
            "action_plan":        advice.get("action_plan", []),
            "context_used": {
                "ats_score_available":    ats_score is not None,
                "market_data_available":  market_insights is not None,
                "personalisation_active": user_profile is not None,
                "job_matches_count":      len(job_matches) if job_matches else 0,
            },
        }

    # ── Internal ───────────────────────────────────────────────────────────────

    def _extract_skills(self, resume_text: str) -> List[str]:
        text_lower = resume_text.lower()
        return sorted(
            s for s in settings.TECH_SKILLS
            if re.search(r"\b" + re.escape(s.lower()) + r"\b", text_lower)
        )

    def _build_context_blocks(
        self,
        job_matches: Optional[List[Dict]],
        ats_score: Optional[Dict],
        market_insights: Optional[Dict],
        user_profile: Optional[Dict],
    ) -> tuple:
        """Return (job_context, ats_context, market_context, profile_context)."""
        job_ctx = ""
        if job_matches:
            job_ctx = "\n".join(
                f"- {j['title']} at {j['company']} (Match: {j.get('match_score', 0)}%)"
                for j in job_matches[:3]
            )

        ats_ctx = ""
        if ats_score:
            missing = ", ".join(ats_score.get("missing_keywords", [])[:4])
            ats_ctx = (
                f"ATS Score: {ats_score.get('overall_score', '?')}/100 "
                f"({ats_score.get('ats_verdict', '')}). "
                f"Missing: {missing}."
            )

        mkt_ctx = ""
        if market_insights:
            mkt_ctx = str(market_insights.get("analysis", ""))[:400]
            hot = market_insights.get("hot_skills", [])
            if hot:
                mkt_ctx += f"\nHot skills: {', '.join(hot[:5])}."

        prof_ctx = ""
        if user_profile and user_profile.get("total_signals", 0) >= 3:
            top_roles = sorted(
                user_profile.get("preferred_roles", {}).items(),
                key=lambda x: x[1], reverse=True,
            )[:3]
            top_skills = sorted(
                user_profile.get("skill_interest", {}).items(),
                key=lambda x: x[1], reverse=True,
            )[:5]
            seniority = user_profile.get("seniority_signal", "unknown")
            prof_ctx = (
                f"Interests: {', '.join(r for r, _ in top_roles)}. "
                f"Skill signals: {', '.join(s for s, _ in top_skills)}. "
                f"Seniority: {seniority}."
            )

        return job_ctx, ats_ctx, mkt_ctx, prof_ctx

    def _generate_advice(
        self,
        resume_text: str,
        current_role: Optional[str],
        target_role: str,
        current_skills: List[str],
        job_matches: Optional[List[Dict]],
        ats_score: Optional[Dict],
        market_insights: Optional[Dict],
        user_profile: Optional[Dict],
    ) -> Dict:
        job_ctx, ats_ctx, mkt_ctx, prof_ctx = self._build_context_blocks(
            job_matches, ats_score, market_insights, user_profile
        )

        system, user = Prompts.career_advice(
            resume_text=resume_text,
            target_role=target_role,
            current_role=current_role,
            job_context=job_ctx,
            ats_context=ats_ctx,
            market_context=mkt_ctx,
            profile_context=prof_ctx,
        )

        try:
            raw = ai_pipeline.call_smart(
                system, user,
                temp=0.7,
                max_tokens=settings.MAX_TOKENS_CAREER_ADVICE,
                use_cache=False,  # career advice should always be fresh
            )
            return self._parse_response(raw.strip(), current_skills)
        except LLMUnavailableError as exc:
            logger.error("Career advice LLM unavailable: %s", exc)
            return self._fallback_advice(current_skills, target_role)
        except Exception as exc:
            logger.error("Career advice error: %s", exc, exc_info=True)
            return self._fallback_advice(current_skills, target_role)

    def _parse_response(self, text: str, current_skills: List[str]) -> Dict:
        lines = text.split("\n")
        assessment, skill_gaps, market_insights, action_plan = "", [], "", []
        section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue
            ll = line.lower()
            if "current assessment" in ll or ll.startswith("1."):
                section = "assessment"
                continue
            elif "skill gap" in ll or "critical skill" in ll or ll.startswith("2."):
                section = "skills"
                continue
            elif "market insight" in ll or ll.startswith("3."):
                section = "market"
                continue
            elif "action plan" in ll or ll.startswith("4."):
                section = "actions"
                continue

            if line.startswith(("**", "#")):
                continue

            if section == "assessment" and not line.startswith("-") and len(line) > 10:
                assessment += line + " "
            elif section == "skills" and line.startswith("-"):
                parts = re.sub(r"^[-•*\s]+", "", line).split("|")
                skill_name    = parts[0].strip()
                importance    = "Critical"
                current_level = "None"
                target_level  = "Intermediate"
                for p in parts[1:]:
                    p = p.strip()
                    if p.lower().startswith("importance"):
                        importance    = p.split(":")[-1].strip()
                    elif p.lower().startswith("current"):
                        current_level = p.split(":")[-1].strip()
                    elif p.lower().startswith("target"):
                        target_level  = p.split(":")[-1].strip()
                if skill_name and len(skill_name) > 2:
                    skill_gaps.append({
                        "skill":         skill_name,
                        "importance":    importance,
                        "current_level": current_level,
                        "target_level":  target_level,
                    })
            elif section == "market" and not line.startswith("-") and len(line) > 10:
                market_insights += line + " "
            elif section == "actions" and (
                line.startswith("-") or (line[0].isdigit() and "." in line[:3])
            ):
                action = re.sub(r"^[-•*\d.)\s]+", "", line).strip()
                if action and len(action) > 5:
                    action_plan.append(action)

        return {
            "assessment": assessment.strip()
                or "Ready to advance with focused skill development.",
            "skill_gaps": skill_gaps[:5] or [{
                "skill":         "System Design",
                "importance":    "Critical",
                "current_level": "Beginner",
                "target_level":  "Intermediate",
            }],
            "market_insights": market_insights.strip()
                or "Strong demand for technical roles in the current market.",
            "action_plan": action_plan[:6] or [
                "Build 2-3 portfolio projects",
                "Practice coding problems daily",
                "Network with professionals on LinkedIn",
                "Apply to 5-10 relevant positions weekly",
            ],
        }

    def _fallback_advice(self, current_skills: List[str], target_role: Optional[str]) -> Dict:
        return {
            "assessment": (
                f"You have {len(current_skills)} relevant skills identified. "
                "Focus on building practical experience through projects."
            ),
            "skill_gaps": [
                {"skill": "System Design",    "importance": "Critical",
                 "current_level": "Beginner", "target_level": "Intermediate"},
                {"skill": "Cloud Platforms",  "importance": "Important",
                 "current_level": "None",     "target_level": "Beginner"},
            ],
            "market_insights": (
                f"Strong market demand for {target_role or 'software engineering'} roles."
            ),
            "action_plan": [
                "Complete 2-3 portfolio projects",
                "Contribute to open-source projects",
                "Build your LinkedIn profile",
                "Practice interview questions daily",
            ],
        }

    def _build_learning_path(self, skill_gaps: List[Dict]) -> List[Dict]:
        """Build a curated resource list from skill gaps."""
        _resource_db: Dict[str, List[Dict]] = {
            "python": [{"title": "Python for Everybody", "type": "Course",
                        "url": "https://coursera.org/specializations/python",
                        "duration": "4 months", "difficulty": "Beginner"}],
            "machine learning": [{"title": "ML by Andrew Ng", "type": "Course",
                                   "url": "https://coursera.org/learn/machine-learning",
                                   "duration": "11 weeks", "difficulty": "Intermediate"}],
            "system design": [{"title": "Grokking System Design", "type": "Course",
                                "url": "https://educative.io/courses/grokking-the-system-design-interview",
                                "duration": "8 weeks", "difficulty": "Advanced"}],
            "docker": [{"title": "Docker Official Docs", "type": "Docs",
                        "url": "https://docs.docker.com/get-started/",
                        "duration": "3 hours", "difficulty": "Beginner"}],
            "react": [{"title": "React – The Complete Guide", "type": "Course",
                       "url": "https://udemy.com/course/react-the-complete-guide/",
                       "duration": "40 hours", "difficulty": "Intermediate"}],
        }
        resources: List[Dict] = []
        for gap in skill_gaps[:5]:
            skill = gap.get("skill", "").lower()
            for key, res_list in _resource_db.items():
                if key in skill or skill in key:
                    resources.extend(res_list)
                    break
            else:
                q = skill.replace(" ", "+")
                resources.append({
                    "title": f"Learn {gap['skill'].title()}",
                    "type": "Course",
                    "url": f"https://coursera.org/search?query={q}",
                    "duration": "Varies",
                    "difficulty": "Intermediate",
                })
        return resources[:10]

    @staticmethod
    def _career_stages() -> List[Dict]:
        return [
            {"role": "Entry Level", "timeline": "0–2 years",
             "key_skills_needed": ["Core technical skills", "Communication", "Problem-solving"],
             "typical_responsibilities": ["Learn and contribute", "Complete assigned tasks"]},
            {"role": "Mid Level", "timeline": "2–5 years",
             "key_skills_needed": ["Advanced skills", "Project ownership", "Mentoring"],
             "typical_responsibilities": ["Lead small projects", "Mentor juniors"]},
            {"role": "Senior Level", "timeline": "5+ years",
             "key_skills_needed": ["Architecture", "Leadership", "Strategy"],
             "typical_responsibilities": ["Design systems", "Guide team direction"]},
        ]


# ── Singleton ─────────────────────────────────────────────────────────────────

_career_advisor: Optional[CareerAdvisor] = None


def get_career_advisor() -> CareerAdvisor:
    global _career_advisor
    if _career_advisor is None:
        _career_advisor = CareerAdvisor()
    return _career_advisor


career_advisor = get_career_advisor()
