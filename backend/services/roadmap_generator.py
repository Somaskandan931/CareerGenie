from groq import Groq
from typing import List, Dict, Optional
import logging
import json
import re

from backend.config import settings

logger = logging.getLogger(__name__)


class RoadmapGenerator:
    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not configured")
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    def generate_roadmap(self, resume_text: str, target_role: str, skill_gaps: List[str],
                          duration_weeks: int = 12, experience_level: Optional[str] = None) -> Dict:
        logger.info(f"Generating {duration_weeks}-week roadmap for: {target_role}")

        prompt = f"""You are a career coach and curriculum designer.

Candidate wants to become: "{target_role}"
Resume excerpt: {resume_text[:1000]}
Skill gaps to address: {', '.join(skill_gaps) if skill_gaps else 'general upskilling'}
Duration: {duration_weeks} weeks
Experience level: {experience_level or 'not specified'}

Respond ONLY with a valid JSON object with this exact structure:
{{
  "title": "{duration_weeks}-Week Path to {target_role}",
  "target_role": "{target_role}",
  "duration_weeks": {duration_weeks},
  "total_hours_estimated": <integer>,
  "summary": "<2-3 sentence overview>",
  "phases": [
    {{
      "phase_number": 1,
      "phase_title": "<e.g. Foundations>",
      "weeks": "1-3",
      "focus": "<focus area>",
      "weekly_tasks": [
        {{
          "week": 1,
          "topic": "<topic>",
          "description": "<what to learn and do>",
          "resources": [
            {{"title": "<name>", "type": "course|book|docs|video|practice", "url": "<url or null>", "duration": "<e.g. 4 hours>"}}
          ],
          "milestone": "<what to achieve by end of week>",
          "hours_per_week": <integer>
        }}
      ]
    }}
  ],
  "final_milestone": "<what candidate builds/achieves at end>",
  "tips": ["<tip 1>", "<tip 2>", "<tip 3>"]
}}

Use real resource names (Coursera, fast.ai, official docs, YouTube). Make it specific and actionable."""

        try:
            response = self.client.chat.completions.create(
                model=settings.GROQ_SMART_MODEL,
                max_tokens=settings.MAX_TOKENS_ROADMAP,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response.choices[0].message.content.strip()
            raw = re.sub(r"^```json\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            roadmap = json.loads(raw)
            logger.info(f"Roadmap generated: {len(roadmap.get('phases', []))} phases")
            return roadmap
        except json.JSONDecodeError as e:
            logger.error(f"Roadmap JSON parse error: {e}")
            return self._fallback_roadmap(target_role, skill_gaps, duration_weeks)
        except Exception as e:
            logger.error(f"Roadmap generation error: {e}")
            raise Exception(f"Roadmap generation failed: {str(e)}")

    def _fallback_roadmap(self, target_role, skill_gaps, duration_weeks):
        weeks_per = max(1, duration_weeks // max(len(skill_gaps), 1))
        phases = []
        for i, skill in enumerate(skill_gaps[:4]):
            sw = i * weeks_per + 1
            ew = sw + weeks_per - 1
            phases.append({
                "phase_number": i + 1, "phase_title": f"Learn {skill.title()}",
                "weeks": f"{sw}-{ew}", "focus": skill,
                "weekly_tasks": [{"week": sw, "topic": skill.title(),
                                   "description": f"Study core concepts of {skill}",
                                   "resources": [{"title": f"{skill.title()} Documentation",
                                                   "type": "docs", "url": None, "duration": "5 hours"}],
                                   "milestone": f"Complete a small {skill} project", "hours_per_week": 8}]
            })
        return {
            "title": f"{duration_weeks}-Week Path to {target_role}",
            "target_role": target_role, "duration_weeks": duration_weeks,
            "total_hours_estimated": duration_weeks * 8,
            "summary": f"A structured plan to become a {target_role}.",
            "phases": phases, "final_milestone": f"Build a {target_role} portfolio project.",
            "tips": ["1 hour daily consistently.", "Build projects — don't just watch tutorials.",
                      "Share progress on LinkedIn or GitHub."]
        }


_roadmap_generator = None

def get_roadmap_generator() -> RoadmapGenerator:
    global _roadmap_generator
    if _roadmap_generator is None:
        _roadmap_generator = RoadmapGenerator()
    return _roadmap_generator