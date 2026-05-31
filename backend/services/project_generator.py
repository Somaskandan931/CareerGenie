"""
backend/services/project_generator.py
========================================
Portfolio project suggestions generator.

Refactored to:
  - Route all LLM calls through ``backend.core.ai_pipeline``
  - Use centralized prompts from ``backend.core.prompts``
  - Sanitize user-supplied resume text
  - Use structured logging via ``backend.core.logging``
"""
from __future__ import annotations

from typing import Dict, List, Optional

from backend.core import ai_pipeline
from backend.core.config import settings
from backend.core.exceptions import LLMUnavailableError
from backend.core.logging import get_logger
from backend.core.prompts import Prompts

logger = get_logger("project_generator")

DEFAULT_SKILLS = ["Python", "System Design", "REST APIs", "Testing", "Docker"]


class ProjectGenerator:

    def suggest_projects(
        self,
        resume_text: str,
        target_role: str,
        skill_gaps: List[str],
        difficulty: Optional[str] = "intermediate",
        num_projects: int = 5,
    ) -> List[Dict]:
        logger.info("Generating %d projects for: %s", num_projects, target_role)

        safe_resume = ai_pipeline.sanitize_user_content(resume_text, max_length=800)
        effective_gaps = skill_gaps if skill_gaps else DEFAULT_SKILLS

        system, user = Prompts.suggest_projects(
            resume_text=safe_resume,
            target_role=target_role,
            skill_gaps=effective_gaps,
            difficulty=difficulty or "intermediate",
            num_projects=num_projects,
        )

        try:
            projects = ai_pipeline.call_json(
                system, user,
                temp=0.7,
                max_tokens=settings.MAX_TOKENS_ROADMAP,
                smart=True,
            )
            if not isinstance(projects, list):
                logger.error("LLM returned JSON but it is not a list")
                return self._fallback_projects(target_role, effective_gaps, num_projects)

            logger.info("Generated %d projects", len(projects))
            return projects

        except Exception as exc:
            logger.error("Project generation error: %s", exc, exc_info=True)
            return self._fallback_projects(target_role, effective_gaps, num_projects)

    def _fallback_projects(
        self,
        target_role: str,
        skill_gaps: List[str],
        num_projects: int,
    ) -> List[Dict]:
        gaps = skill_gaps if skill_gaps else DEFAULT_SKILLS
        while len(gaps) < num_projects:
            gaps = gaps + DEFAULT_SKILLS

        return [
            {
                "id":               f"project_{i + 1}",
                "title":            f"{s.title()} Showcase App",
                "tagline":          f"Demonstrates {s} skills.",
                "difficulty":       "intermediate",
                "estimated_weeks":  2,
                "hours_per_week":   8,
                "tech_stack":       [s, "Python", "FastAPI"],
                "skills_covered":   [s],
                "skills_from_gaps": [s],
                "description":      f"Build a real-world {s} application to demonstrate practical ability.",
                "key_features":     ["Core functionality", "Documentation", "Tests"],
                "learning_outcomes": [f"Hands-on {s} experience"],
                "impact_statement": f"Shows practical {s} ability to {target_role} hiring managers.",
                "github_template":  None,
                "bonus_extensions": ["Add a dashboard", "Deploy to cloud"],
            }
            for i, s in enumerate(gaps[:num_projects])
        ]


# ── Singleton ──────────────────────────────────────────────────────────────────

_project_generator: Optional[ProjectGenerator] = None


def get_project_generator() -> ProjectGenerator:
    global _project_generator
    if _project_generator is None:
        _project_generator = ProjectGenerator()
    return _project_generator
