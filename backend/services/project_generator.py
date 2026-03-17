from anthropic import Anthropic
from typing import List, Dict, Optional
import logging
import json
import re

from backend.config import settings

logger = logging.getLogger(__name__)


class ProjectGenerator:
    """
    Suggests hands-on portfolio projects tailored to the user's skill gaps
    and target role, using Claude AI.
    """

    def __init__(self):
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not configured")

        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        # GitHub template repos by domain (extend as needed)
        self.github_templates = {
            "machine learning": "https://github.com/topics/machine-learning-project",
            "web": "https://github.com/topics/web-app",
            "data": "https://github.com/topics/data-science-project",
            "devops": "https://github.com/topics/devops",
            "api": "https://github.com/topics/rest-api",
            "nlp": "https://github.com/topics/nlp",
            "computer vision": "https://github.com/topics/computer-vision",
        }

    def suggest_projects(
        self,
        resume_text: str,
        target_role: str,
        skill_gaps: List[str],
        difficulty: Optional[str] = "intermediate",
        num_projects: int = 5,
    ) -> List[Dict]:
        """
        Generate portfolio project suggestions based on skill gaps.

        Args:
            resume_text: Candidate's resume text
            target_role: The job role the candidate is targeting
            skill_gaps: Skills to address through projects
            difficulty: "beginner", "intermediate", or "advanced"
            num_projects: How many projects to suggest

        Returns:
            List of project suggestion dicts
        """
        logger.info(f"Generating {num_projects} project suggestions for: {target_role}")

        resume_preview = resume_text[:1000]
        gaps_str = ", ".join(skill_gaps) if skill_gaps else "general skills"

        prompt = f"""You are an expert software engineering mentor specializing in portfolio projects.

A candidate is targeting the role of "{target_role}".

Their background (resume excerpt):
{resume_preview}

Skills to develop through projects: {gaps_str}
Preferred difficulty: {difficulty}
Number of projects requested: {num_projects}

Suggest {num_projects} hands-on portfolio projects. Respond ONLY with a valid JSON array:

[
  {{
    "id": "project_1",
    "title": "<catchy project title>",
    "tagline": "<one-sentence description>",
    "difficulty": "beginner|intermediate|advanced",
    "estimated_weeks": <integer>,
    "hours_per_week": <integer>,
    "tech_stack": ["<tech1>", "<tech2>", "<tech3>"],
    "skills_covered": ["<skill1>", "<skill2>"],
    "skills_from_gaps": ["<which gap skills this addresses>"],
    "description": "<2-3 sentences describing the project, what it does, and what the candidate will build>",
    "key_features": ["<feature 1>", "<feature 2>", "<feature 3>"],
    "learning_outcomes": ["<what they will learn>"],
    "impact_statement": "<1 sentence: why this project impresses recruiters for this specific role>",
    "github_template": "<relevant GitHub search URL or null>",
    "bonus_extensions": ["<optional extension idea 1>", "<optional extension idea 2>"]
  }}
]

Make projects SPECIFIC and REAL — no generic to-do apps. Each project should directly address the skill gaps and be something a {target_role} would actually build. Vary complexity across the list."""

        try:
            response = self.client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=getattr(settings, "MAX_TOKENS_ROADMAP", 3000),
                messages=[{"role": "user", "content": prompt}],
            )

            raw = response.content[0].text.strip()
            raw = re.sub(r"^```json\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

            projects = json.loads(raw)
            logger.info(f"Generated {len(projects)} project suggestions")
            return projects

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse projects JSON: {e}")
            return self._fallback_projects(target_role, skill_gaps, num_projects)

        except Exception as e:
            logger.error(f"Error generating projects: {e}")
            raise Exception(f"Project generation failed: {str(e)}")

    def _fallback_projects(
        self, target_role: str, skill_gaps: List[str], num_projects: int
    ) -> List[Dict]:
        """Return basic fallback projects if Claude's response fails to parse."""
        fallback = []
        for i, skill in enumerate(skill_gaps[:num_projects]):
            fallback.append(
                {
                    "id": f"project_{i + 1}",
                    "title": f"{skill.title()} Showcase App",
                    "tagline": f"A practical application demonstrating {skill} skills.",
                    "difficulty": "intermediate",
                    "estimated_weeks": 2,
                    "hours_per_week": 8,
                    "tech_stack": [skill, "Python", "FastAPI"],
                    "skills_covered": [skill],
                    "skills_from_gaps": [skill],
                    "description": f"Build a real-world application using {skill} to demonstrate your ability to a hiring manager.",
                    "key_features": [
                        "Core functionality",
                        "Documentation",
                        "Tests",
                    ],
                    "learning_outcomes": [f"Hands-on experience with {skill}"],
                    "impact_statement": f"Shows practical {skill} ability to {target_role} hiring managers.",
                    "github_template": None,
                    "bonus_extensions": ["Add a dashboard", "Deploy to cloud"],
                }
            )
        return fallback


# Singleton instance
_project_generator = None


def get_project_generator() -> ProjectGenerator:
    global _project_generator
    if _project_generator is None:
        _project_generator = ProjectGenerator()
    return _project_generator