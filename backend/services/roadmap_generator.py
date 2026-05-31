"""
backend/services/roadmap_generator.py
========================================
Learning roadmap generator.

Refactored to:
  - Route all LLM calls through ``backend.core.ai_pipeline``
  - Use centralized prompts from ``backend.core.prompts``
  - Sanitize user-supplied resume text
  - Use structured logging via ``backend.core.logging``
  - Reliable resource DB preserved for URL injection into prompts
"""
from __future__ import annotations

from typing import Dict, List, Optional

from backend.core import ai_pipeline
from backend.core.config import settings
from backend.core.logging import get_logger
from backend.core.prompts import Prompts

logger = get_logger("roadmap_generator")

# Reliable resource database with working URLs
RELIABLE_RESOURCES: Dict[str, List[Dict]] = {
    "python": [
        {"title": "Python for Everybody", "type": "course",
         "url": "https://www.coursera.org/specializations/python",
         "duration": "4 months", "difficulty": "Beginner"},
        {"title": "Python Official Tutorial", "type": "docs",
         "url": "https://docs.python.org/3/tutorial/",
         "duration": "10 hours", "difficulty": "Beginner"},
    ],
    "pytorch": [
        {"title": "PyTorch Official Tutorials", "type": "docs",
         "url": "https://pytorch.org/tutorials/",
         "duration": "15 hours", "difficulty": "Intermediate"},
    ],
    "tensorflow": [
        {"title": "TensorFlow Official Tutorials", "type": "docs",
         "url": "https://www.tensorflow.org/tutorials",
         "duration": "12 hours", "difficulty": "Intermediate"},
        {"title": "Deep Learning Specialization", "type": "course",
         "url": "https://www.coursera.org/specializations/deep-learning",
         "duration": "6 months", "difficulty": "Advanced"},
    ],
    "machine learning": [
        {"title": "Machine Learning by Andrew Ng", "type": "course",
         "url": "https://www.coursera.org/learn/machine-learning",
         "duration": "11 weeks", "difficulty": "Intermediate"},
    ],
    "docker": [
        {"title": "Docker Curriculum", "type": "course",
         "url": "https://docker-curriculum.com/",
         "duration": "4 hours", "difficulty": "Beginner"},
        {"title": "Docker Official Docs", "type": "docs",
         "url": "https://docs.docker.com/get-started/",
         "duration": "3 hours", "difficulty": "Beginner"},
    ],
    "kubernetes": [
        {"title": "Kubernetes Basics", "type": "docs",
         "url": "https://kubernetes.io/docs/tutorials/kubernetes-basics/",
         "duration": "6 hours", "difficulty": "Intermediate"},
    ],
    "aws": [
        {"title": "AWS Certified Cloud Practitioner", "type": "course",
         "url": "https://aws.amazon.com/certification/certified-cloud-practitioner/",
         "duration": "20 hours", "difficulty": "Beginner"},
    ],
    "system design": [
        {"title": "Grokking System Design", "type": "course",
         "url": "https://www.educative.io/courses/grokking-the-system-design-interview",
         "duration": "8 weeks", "difficulty": "Advanced"},
        {"title": "System Design Primer", "type": "github",
         "url": "https://github.com/donnemartin/system-design-primer",
         "duration": "20 hours", "difficulty": "Intermediate"},
    ],
    "sql": [
        {"title": "SQL Tutorial", "type": "course",
         "url": "https://www.w3schools.com/sql/",
         "duration": "5 hours", "difficulty": "Beginner"},
    ],
    "bms": [
        {"title": "Battery Management Systems", "type": "course",
         "url": "https://www.udemy.com/course/battery-management-systems/",
         "duration": "10 hours", "difficulty": "Intermediate"},
    ],
    "can bus": [
        {"title": "CAN Bus Explained", "type": "tutorial",
         "url": "https://www.csselectronics.com/pages/can-bus-tutorial",
         "duration": "2 hours", "difficulty": "Intermediate"},
    ],
    "plc": [
        {"title": "PLC Programming", "type": "course",
         "url": "https://www.plcacademy.com/",
         "duration": "15 hours", "difficulty": "Beginner"},
    ],
}


class RoadmapGenerator:

    def _get_reliable_resources(self, topic: str) -> List[Dict]:
        topic_lower = topic.lower()
        if topic_lower in RELIABLE_RESOURCES:
            return RELIABLE_RESOURCES[topic_lower]
        for key, resources in RELIABLE_RESOURCES.items():
            if key in topic_lower or topic_lower in key:
                return resources
        query = topic.replace(" ", "+")
        return [
            {"title": f"Learn {topic}", "type": "course",
             "url": f"https://www.coursera.org/search?query={query}",
             "duration": "Varies", "difficulty": "Intermediate"},
            {"title": f"{topic} Documentation", "type": "docs",
             "url": f"https://www.google.com/search?q={query}+documentation",
             "duration": "Varies", "difficulty": "Intermediate"},
        ]

    def _fix_resource_urls(self, roadmap: Dict) -> None:
        """Post-process roadmap in-place: replace missing/null resource URLs."""
        for phase in roadmap.get("phases", []):
            for task in phase.get("weekly_tasks", []):
                for resource in task.get("resources", []):
                    url = resource.get("url")
                    if not url or url == "null":
                        reliable = self._get_reliable_resources(task.get("topic", ""))
                        if reliable:
                            resource["url"] = reliable[0]["url"]

    def _build_resources_section(self, skill_gaps: List[str]) -> str:
        """Build a curated resources block to inject into the prompt."""
        lines = []
        for skill in skill_gaps[:3]:
            resources = self._get_reliable_resources(skill)
            lines.append(f"\nFor {skill}:")
            for r in resources[:2]:
                lines.append(f"- {r['title']} ({r['type']}) - {r['url']}")
        return "\n".join(lines)

    def generate_roadmap(
        self,
        resume_text: str,
        target_role: str,
        skill_gaps: List[str],
        duration_weeks: int = 12,
        experience_level: Optional[str] = None,
    ) -> Dict:
        logger.info("Generating %d-week roadmap for: %s", duration_weeks, target_role)

        safe_resume = ai_pipeline.sanitize_user_content(resume_text, max_length=1000)
        effective_gaps = skill_gaps if skill_gaps else ["general software engineering skills"]
        resources_section = self._build_resources_section(effective_gaps)

        system, user = Prompts.generate_roadmap(
            resume_text=safe_resume,
            target_role=target_role,
            skill_gaps=effective_gaps,
            duration_weeks=duration_weeks,
            resources_section=resources_section,
        )

        try:
            roadmap = ai_pipeline.call_json(
                system, user,
                temp=0.7,
                max_tokens=settings.MAX_TOKENS_ROADMAP,
                smart=True,
            )
            if not isinstance(roadmap, dict):
                logger.error("LLM returned JSON but it is not an object")
                return self._fallback_roadmap(target_role, effective_gaps, duration_weeks)

            self._fix_resource_urls(roadmap)
            logger.info("Roadmap generated: %d phases", len(roadmap.get("phases", [])))
            return roadmap

        except Exception as exc:
            logger.error("Roadmap generation error: %s", exc, exc_info=True)
            return self._fallback_roadmap(target_role, effective_gaps, duration_weeks)

    def _fallback_roadmap(
        self,
        target_role: str,
        skill_gaps: List[str],
        duration_weeks: int,
    ) -> Dict:
        gaps = skill_gaps if skill_gaps else ["general software engineering skills"]
        weeks_per = max(1, duration_weeks // max(len(gaps), 1))
        phases = []

        for i, skill in enumerate(gaps[:4]):
            sw = i * weeks_per + 1
            ew = sw + weeks_per - 1
            resources = self._get_reliable_resources(skill)
            phases.append({
                "phase_number": i + 1,
                "phase_title": f"Learn {skill.title()}",
                "weeks": f"{sw}-{ew}",
                "focus": skill,
                "weekly_tasks": [{
                    "week": sw,
                    "topic": skill.title(),
                    "description": f"Study core concepts of {skill}",
                    "resources": resources[:2],
                    "milestone": f"Complete a small {skill} project",
                    "hours_per_week": 8,
                }],
            })

        return {
            "title": f"{duration_weeks}-Week Path to {target_role}",
            "target_role": target_role,
            "duration_weeks": duration_weeks,
            "total_hours_estimated": duration_weeks * 8,
            "summary": f"A structured plan to become a {target_role}.",
            "phases": phases,
            "final_milestone": f"Build a {target_role} portfolio project.",
            "tips": [
                "1 hour daily beats occasional marathon sessions.",
                "Build projects — don't just watch tutorials.",
                "Share progress on LinkedIn or GitHub.",
            ],
        }


# ── Singleton ──────────────────────────────────────────────────────────────────

_roadmap_generator: Optional[RoadmapGenerator] = None


def get_roadmap_generator() -> RoadmapGenerator:
    global _roadmap_generator
    if _roadmap_generator is None:
        _roadmap_generator = RoadmapGenerator()
    return _roadmap_generator
