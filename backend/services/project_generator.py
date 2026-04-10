from typing import List, Dict, Optional
import logging
import json
import re

from backend.config import settings
from backend.services.llm import llm_call_sync, llm_call_smart_sync


logger = logging.getLogger(__name__)

DEFAULT_SKILLS = ["Python", "System Design", "REST APIs", "Testing", "Docker"]


class ProjectGenerator:
    def __init__(self):
        pass

    def suggest_projects(
        self,
        resume_text: str,
        target_role: str,
        skill_gaps: List[str],
        difficulty: Optional[str] = "intermediate",
        num_projects: int = 5,
    ) -> List[Dict]:
        logger.info(f"Generating {num_projects} projects for: {target_role}")

        effective_gaps = skill_gaps if skill_gaps else DEFAULT_SKILLS

        prompt = f"""You are a software engineering mentor specializing in portfolio projects.

Candidate targeting: "{target_role}"
Background: {resume_text[:800]}
Skills to develop: {', '.join(effective_gaps)}
Difficulty: {difficulty}

Suggest {num_projects} hands-on portfolio projects. Respond ONLY with a valid JSON array (no markdown fences, no explanation):
[
  {{
    "id": "project_1",
    "title": "<catchy title>",
    "tagline": "<one sentence>",
    "difficulty": "beginner|intermediate|advanced",
    "estimated_weeks": <integer>,
    "hours_per_week": <integer>,
    "tech_stack": ["<tech1>", "<tech2>"],
    "skills_covered": ["<skill1>"],
    "skills_from_gaps": ["<gap skill addressed>"],
    "description": "<2-3 sentences: what it is and what candidate builds>",
    "key_features": ["<feature 1>", "<feature 2>", "<feature 3>"],
    "learning_outcomes": ["<outcome 1>", "<outcome 2>"],
    "impact_statement": "<why this impresses recruiters for this role>",
    "github_template": null,
    "bonus_extensions": ["<extension 1>", "<extension 2>"]
  }}
]

Make projects SPECIFIC and REAL — no generic to-do apps. Each project should address the skill gaps.
Return ONLY the JSON array. Do not wrap it in markdown code fences."""

        try:
            raw = llm_call_smart_sync(
                system="You are an expert AI assistant. Respond ONLY with valid JSON. No markdown, no preamble.",
                user=prompt,
                temp=0.7,
                max_tokens=settings.MAX_TOKENS_ROADMAP,
            )

            # Strip markdown fences if model included them anyway
            raw = raw.strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
            raw = re.sub(r"\s*```\s*$", "", raw, flags=re.MULTILINE)
            raw = raw.strip()

            # Find the start of the JSON array (guard against preamble text)
            bracket_idx = raw.find("[")
            if bracket_idx == -1:
                logger.error("No JSON array found in LLM response")
                logger.debug(f"Raw response: {raw[:500]}")
                return self._fallback_projects(target_role, effective_gaps, num_projects)
            if bracket_idx > 0:
                raw = raw[bracket_idx:]

            projects = json.loads(raw)

            if not isinstance(projects, list):
                logger.error("LLM returned JSON but it is not a list")
                return self._fallback_projects(target_role, effective_gaps, num_projects)

            logger.info(f"Generated {len(projects)} projects")
            return projects

        except json.JSONDecodeError as e:
            logger.error(f"Project JSON parse error: {e}", exc_info=True)
            return self._fallback_projects(target_role, effective_gaps, num_projects)
        except Exception as e:
            logger.error(f"Project generation error: {e}", exc_info=True)
            raise Exception(f"Project generation failed: {str(e)}")

    def _fallback_projects(
        self, target_role: str, skill_gaps: List[str], num_projects: int
    ) -> List[Dict]:
        """Return safe fallback projects when LLM generation fails."""
        # Ensure we always have something to iterate over
        gaps = skill_gaps if skill_gaps else DEFAULT_SKILLS
        # Pad list if fewer gaps than requested projects
        while len(gaps) < num_projects:
            gaps = gaps + DEFAULT_SKILLS

        return [
            {
                "id": f"project_{i + 1}",
                "title": f"{s.title()} Showcase App",
                "tagline": f"Demonstrates {s} skills.",
                "difficulty": "intermediate",
                "estimated_weeks": 2,
                "hours_per_week": 8,
                "tech_stack": [s, "Python", "FastAPI"],
                "skills_covered": [s],
                "skills_from_gaps": [s],
                "description": f"Build a real-world {s} application to demonstrate practical ability.",
                "key_features": ["Core functionality", "Documentation", "Tests"],
                "learning_outcomes": [f"Hands-on {s} experience"],
                "impact_statement": (
                    f"Shows practical {s} ability to {target_role} hiring managers."
                ),
                "github_template": None,
                "bonus_extensions": ["Add a dashboard", "Deploy to cloud"],
            }
            for i, s in enumerate(gaps[:num_projects])
        ]


_project_generator = None


def get_project_generator() -> ProjectGenerator:
    global _project_generator
    if _project_generator is None:
        _project_generator = ProjectGenerator()
    return _project_generator