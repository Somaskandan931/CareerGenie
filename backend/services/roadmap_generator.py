from anthropic import Anthropic
from typing import List, Dict, Optional
import logging
import json
import re

from backend.config import settings

logger = logging.getLogger(__name__)


class RoadmapGenerator:
    """
    Generates personalized, week-by-week career roadmaps using Claude AI.
    Each roadmap is driven by the user's actual skill gaps and target role.
    """

    def __init__(self):
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not configured")

        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def generate_roadmap(
        self,
        resume_text: str,
        target_role: str,
        skill_gaps: List[str],
        duration_weeks: int = 12,
        experience_level: Optional[str] = None,
    ) -> Dict:
        """
        Generate a structured week-by-week learning roadmap.

        Args:
            resume_text: Candidate's resume text
            target_role: The job role the candidate is targeting
            skill_gaps: List of skills the candidate needs to develop
            duration_weeks: How many weeks the roadmap should span
            experience_level: "entry", "mid", or "senior"

        Returns:
            Structured roadmap dict with weeks, milestones, and resources
        """
        logger.info(f"Generating {duration_weeks}-week roadmap for: {target_role}")

        resume_preview = resume_text[:1500]
        gaps_str = ", ".join(skill_gaps) if skill_gaps else "general upskilling"

        prompt = f"""You are an expert career coach and curriculum designer.

A candidate wants to become a "{target_role}".

Their resume summary:
{resume_preview}

Skill gaps to address: {gaps_str}
Roadmap duration: {duration_weeks} weeks
Experience level: {experience_level or "not specified"}

Generate a detailed, realistic week-by-week roadmap. Respond ONLY with a valid JSON object matching this exact structure:

{{
  "title": "X-Week Path to [Role]",
  "target_role": "{target_role}",
  "duration_weeks": {duration_weeks},
  "total_hours_estimated": <integer>,
  "summary": "<2-3 sentence overview of the roadmap strategy>",
  "phases": [
    {{
      "phase_number": 1,
      "phase_title": "<phase name, e.g. 'Foundations'>",
      "weeks": "1-3",
      "focus": "<what this phase focuses on>",
      "weekly_tasks": [
        {{
          "week": 1,
          "topic": "<topic name>",
          "description": "<what to learn and do this week>",
          "resources": [
            {{"title": "<resource name>", "type": "course|book|docs|video|practice", "url": "<url or null>", "duration": "<e.g. 4 hours>"}}
          ],
          "milestone": "<what to build or achieve by end of week>",
          "hours_per_week": <integer>
        }}
      ]
    }}
  ],
  "final_milestone": "<What the candidate will have built/achieved by the end>",
  "tips": ["<practical tip 1>", "<practical tip 2>", "<practical tip 3>"]
}}

Make the roadmap specific, actionable, and realistic. Include real resource names (Coursera, fast.ai, official docs, etc.). Vary resource types. End with project-based milestones."""

        try:
            response = self.client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=getattr(settings, "MAX_TOKENS_ROADMAP", 3000),
                messages=[{"role": "user", "content": prompt}],
            )

            raw = response.content[0].text.strip()

            # Strip markdown fences if present
            raw = re.sub(r"^```json\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

            roadmap = json.loads(raw)
            logger.info(f"Roadmap generated: {len(roadmap.get('phases', []))} phases")
            return roadmap

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse roadmap JSON: {e}")
            return self._fallback_roadmap(target_role, skill_gaps, duration_weeks)

        except Exception as e:
            logger.error(f"Error generating roadmap: {e}")
            raise Exception(f"Roadmap generation failed: {str(e)}")

    def _fallback_roadmap(
        self, target_role: str, skill_gaps: List[str], duration_weeks: int
    ) -> Dict:
        """Return a minimal fallback roadmap if Claude's response fails to parse."""
        weeks_per_skill = max(1, duration_weeks // max(len(skill_gaps), 1))
        phases = []

        for i, skill in enumerate(skill_gaps[:4]):
            start_week = i * weeks_per_skill + 1
            end_week = start_week + weeks_per_skill - 1
            phases.append(
                {
                    "phase_number": i + 1,
                    "phase_title": f"Learn {skill.title()}",
                    "weeks": f"{start_week}-{end_week}",
                    "focus": skill,
                    "weekly_tasks": [
                        {
                            "week": start_week,
                            "topic": skill.title(),
                            "description": f"Study core concepts of {skill}",
                            "resources": [
                                {
                                    "title": f"{skill.title()} Official Documentation",
                                    "type": "docs",
                                    "url": None,
                                    "duration": "5 hours",
                                }
                            ],
                            "milestone": f"Complete a small {skill} project",
                            "hours_per_week": 8,
                        }
                    ],
                }
            )

        return {
            "title": f"{duration_weeks}-Week Path to {target_role}",
            "target_role": target_role,
            "duration_weeks": duration_weeks,
            "total_hours_estimated": duration_weeks * 8,
            "summary": f"A structured plan to become a {target_role} by closing your key skill gaps.",
            "phases": phases,
            "final_milestone": f"Build a portfolio project demonstrating {target_role} skills.",
            "tips": [
                "Dedicate at least 1 hour per day consistently.",
                "Build projects — don't just watch tutorials.",
                "Share your progress on LinkedIn or GitHub.",
            ],
        }


# Singleton instance
_roadmap_generator = None


def get_roadmap_generator() -> RoadmapGenerator:
    global _roadmap_generator
    if _roadmap_generator is None:
        _roadmap_generator = RoadmapGenerator()
    return _roadmap_generator