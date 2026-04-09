"""
tools/skill_tool.py
====================
Skill extraction tool — wraps the existing enhanced_skill_extractor and
the regex-based skill matching in config.TECH_SKILLS so agents have a
clean extract_skills(text) interface.

Provides two levels:
  1. Fast regex-based extraction (extract_skills_fast) — uses TECH_SKILLS list
  2. Full NLP extraction (extract_skills) — uses EnhancedSkillExtractor
     which returns richer skill objects with context and proficiency signals
"""
from __future__ import annotations

import logging
import re
from typing import List

logger = logging.getLogger(__name__)


def extract_skills_fast(text: str) -> List[str]:
    """
    Quick regex-based skill extraction using the TECH_SKILLS list in config.py.
    Returns a sorted list of matched skill strings.

    Use this when speed matters more than richness (e.g. inside a scoring loop).
    """
    try:
        from backend.config import settings
        text_lower = text.lower()
        found: set = set()
        for skill in settings.TECH_SKILLS:
            if re.search(r"\b" + re.escape(skill.lower()) + r"\b", text_lower):
                found.add(skill)
        return sorted(found)
    except Exception as e:
        logger.error(f"extract_skills_fast failed: {e}")
        return []


def extract_skills(text: str) -> List[str]:
    """
    Full NLP skill extraction via EnhancedSkillExtractor.
    Returns a list of skill name strings.

    Falls back to extract_skills_fast if the enhanced extractor is unavailable.
    """
    try:
        from backend.services.enhanced_skill_extractor import EnhancedSkillExtractor
        extractor = EnhancedSkillExtractor()
        skill_objects = extractor.extract_skills_with_context(text)
        # Each object may be a dict {skill, proficiency, ...} or a plain string
        skills = []
        for s in skill_objects:
            if isinstance(s, dict):
                skills.append(s.get("skill", ""))
            elif isinstance(s, str):
                skills.append(s)
        return [s for s in skills if s]
    except Exception as e:
        logger.warning(f"EnhancedSkillExtractor unavailable ({e}), using fast fallback")
        return extract_skills_fast(text)


def skills_gap(resume_text: str, job_description: str) -> dict:
    """
    Compute skill gap between a resume and a job description.

    Returns:
        {
            "resume_skills":  list of skills found in resume,
            "job_skills":     list of skills found in JD,
            "matched":        skills in both,
            "missing":        skills in JD but not resume,
            "bonus":          skills in resume but not in JD,
            "match_pct":      float [0, 100],
        }
    """
    resume_skills = set(extract_skills_fast(resume_text))
    job_skills    = set(extract_skills_fast(job_description))

    matched = resume_skills & job_skills
    missing = job_skills - resume_skills
    bonus   = resume_skills - job_skills

    match_pct = (len(matched) / len(job_skills) * 100) if job_skills else 0.0

    return {
        "resume_skills": sorted(resume_skills),
        "job_skills":    sorted(job_skills),
        "matched":       sorted(matched),
        "missing":       sorted(missing),
        "bonus":         sorted(bonus),
        "match_pct":     round(match_pct, 1),
    }
