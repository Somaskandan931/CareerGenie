from groq import Groq
from typing import List, Dict, Optional
import logging
import re

from backend.config import settings

logger = logging.getLogger(__name__)


class CareerAdvisor:
    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not configured")
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        logger.info("CareerAdvisor initialized with Groq")

    def generate_career_advice(self, resume_text: str, target_role: Optional[str] = None,
                                current_role: Optional[str] = None,
                                job_matches: Optional[List[Dict]] = None) -> Dict:
        current_skills = self._extract_skills_from_resume(resume_text)
        advice = self._generate_advice(resume_text, current_role, target_role,
                                        current_skills, job_matches)
        learning_path = self._generate_learning_path(current_skills, target_role,
                                                      advice.get('skill_gaps', []))
        career_progression = self._generate_career_progression(current_role, target_role)
        return {
            "current_assessment": advice.get('assessment', ''),
            "skill_gaps": advice.get('skill_gaps', []),
            "learning_path": learning_path,
            "career_progression": career_progression,
            "market_insights": advice.get('market_insights', ''),
            "action_plan": advice.get('action_plan', [])
        }

    def _extract_skills_from_resume(self, resume_text: str) -> List[str]:
        text_lower = resume_text.lower()
        found = set()
        for skill in settings.TECH_SKILLS:
            if re.search(r'\b' + re.escape(skill.lower()) + r'\b', text_lower):
                found.add(skill)
        return sorted(list(found))

    def _generate_advice(self, resume_text, current_role, target_role,
                          current_skills, job_matches) -> Dict:
        job_context = ""
        if job_matches:
            job_context = "\n".join([
                f"- {j['title']} at {j['company']} (Match: {j.get('match_score', 0)}%)"
                for j in job_matches[:3]
            ])

        prompt = f"""You are an expert career advisor.

Resume: {resume_text[:1200]}
Current Role: {current_role or 'Entry-level'}
Target Role: {target_role or 'Software Engineer'}
Current Skills: {', '.join(current_skills) if current_skills else 'Limited'}
Recent Job Matches: {job_context or 'None'}

Provide structured career advice with these exact sections:

1. CURRENT ASSESSMENT: 2-3 sentences evaluating market readiness and strengths.

2. CRITICAL SKILL GAPS: List exactly 4 missing skills, one per line, format:
- SkillName | Importance: Critical/Important | Current: None/Beginner | Target: Intermediate/Advanced

3. MARKET INSIGHTS: 2 sentences on demand, salary range, trends for target role.

4. ACTION PLAN: 5 specific actionable steps, one per line starting with a dash.

Be direct and specific."""

        try:
            response = self.client.chat.completions.create(
                model=settings.GROQ_SMART_MODEL,
                max_tokens=settings.MAX_TOKENS_CAREER_ADVICE,
                messages=[{"role": "user", "content": prompt}]
            )
            return self._parse_response(response.choices[0].message.content.strip(),
                                         current_skills)
        except Exception as e:
            logger.error(f"Career advice error: {e}")
            return self._fallback_advice(current_skills, target_role)

    def _parse_response(self, text: str, current_skills: List[str]) -> Dict:
        lines = text.split('\n')
        assessment, skill_gaps, market_insights, action_plan = "", [], "", []
        section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue
            ll = line.lower()
            if "current assessment" in ll or ll.startswith("1."):
                section = "assessment"; continue
            elif "skill gap" in ll or "critical skill" in ll or ll.startswith("2."):
                section = "skills"; continue
            elif "market insight" in ll or ll.startswith("3."):
                section = "market"; continue
            elif "action plan" in ll or ll.startswith("4."):
                section = "actions"; continue

            if line.startswith(('**', '#')): continue

            if section == "assessment" and not line.startswith('-') and len(line) > 10:
                assessment += line + " "
            elif section == "skills" and line.startswith('-'):
                parts = re.sub(r'^[-•*\s]+', '', line).split('|')
                skill_name = parts[0].strip()
                importance = "Critical"
                current_level = "None"
                target_level = "Intermediate"
                for p in parts[1:]:
                    p = p.strip()
                    if p.lower().startswith("importance"):
                        importance = p.split(":")[-1].strip()
                    elif p.lower().startswith("current"):
                        current_level = p.split(":")[-1].strip()
                    elif p.lower().startswith("target"):
                        target_level = p.split(":")[-1].strip()
                if skill_name and len(skill_name) > 2:
                    skill_gaps.append({"skill": skill_name, "importance": importance,
                                        "current_level": current_level, "target_level": target_level})
            elif section == "market" and not line.startswith('-') and len(line) > 10:
                market_insights += line + " "
            elif section == "actions" and (line.startswith('-') or (line[0].isdigit() and '.' in line[:3])):
                action = re.sub(r'^[-•*\d.)\s]+', '', line).strip()
                if action and len(action) > 5:
                    action_plan.append(action)

        return {
            "assessment": assessment.strip() or "Ready to advance with focused skill development.",
            "skill_gaps": skill_gaps[:5] or [{"skill": "System Design", "importance": "Critical",
                                               "current_level": "Beginner", "target_level": "Intermediate"}],
            "market_insights": market_insights.strip() or "Strong demand for technical roles.",
            "action_plan": action_plan[:6] or ["Build 2-3 portfolio projects", "Practice coding daily",
                                                "Network with professionals", "Apply to relevant positions weekly"]
        }

    def _fallback_advice(self, current_skills, target_role):
        return {
            "assessment": f"You have {len(current_skills)} relevant skills. Focus on building practical experience.",
            "skill_gaps": [
                {"skill": "System Design", "importance": "Critical", "current_level": "Beginner", "target_level": "Intermediate"},
                {"skill": "Cloud Platforms", "importance": "Important", "current_level": "None", "target_level": "Beginner"},
            ],
            "market_insights": f"Strong market demand for {target_role or 'software engineering'}.",
            "action_plan": ["Complete 2-3 portfolio projects", "Contribute to open source",
                             "Build LinkedIn profile", "Practice interview questions"]
        }

    def _generate_learning_path(self, current_skills, target_role, skill_gaps) -> List[Dict]:
        resources = []
        for gap in skill_gaps[:5]:
            skill = gap['skill'].lower()
            resources.extend(self._get_resources(skill))
        return resources[:10]

    def _get_resources(self, skill: str) -> List[Dict]:
        db = {
            "python": [{"title": "Python for Everybody", "type": "Course",
                         "url": "https://coursera.org/specializations/python", "duration": "4 months", "difficulty": "Beginner"}],
            "machine learning": [{"title": "ML by Andrew Ng", "type": "Course",
                                   "url": "https://coursera.org/learn/machine-learning", "duration": "11 weeks", "difficulty": "Intermediate"}],
            "docker": [{"title": "Docker for Developers", "type": "Course",
                         "url": "https://udemy.com/course/docker-kubernetes/", "duration": "6 hours", "difficulty": "Beginner"}],
            "react": [{"title": "React – The Complete Guide", "type": "Course",
                        "url": "https://udemy.com/course/react-the-complete-guide/", "duration": "40 hours", "difficulty": "Intermediate"}],
            "system design": [{"title": "Grokking System Design", "type": "Course",
                                "url": "https://educative.io/courses/grokking-the-system-design-interview", "duration": "8 weeks", "difficulty": "Advanced"}],
        }
        for key, res in db.items():
            if key in skill or skill in key:
                return res
        return [{"title": f"Learn {skill.title()}", "type": "Course",
                  "url": f"https://coursera.org/search?query={skill.replace(' ', '+')}", "duration": "Varies", "difficulty": "Intermediate"}]

    def _generate_career_progression(self, current_role, target_role) -> List[Dict]:
        return [
            {"role": "Entry Level", "timeline": "0–2 years",
             "key_skills_needed": ["Core technical skills", "Communication", "Problem-solving"],
             "typical_responsibilities": ["Learn and contribute", "Complete assigned tasks"]},
            {"role": "Mid Level", "timeline": "2–5 years",
             "key_skills_needed": ["Advanced skills", "Project ownership", "Collaboration"],
             "typical_responsibilities": ["Lead small projects", "Mentor juniors"]},
            {"role": "Senior Level", "timeline": "5+ years",
             "key_skills_needed": ["Architecture", "Leadership", "Strategy"],
             "typical_responsibilities": ["Design systems", "Guide team direction"]},
        ]


try:
    career_advisor = CareerAdvisor()
except Exception as e:
    logger.error(f"Failed to initialize CareerAdvisor: {e}")
    career_advisor = None