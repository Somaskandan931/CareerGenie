from anthropic import Anthropic
from typing import List, Dict, Optional
import logging
import re

from backend.config import settings

logger = logging.getLogger(__name__)


class CareerAdvisor:
    """Provides comprehensive career guidance, learning paths, and progression advice"""

    def __init__(self):
        """Initialize Anthropic client"""
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not configured")

        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        logger.info("CareerAdvisor initialized")

    def generate_career_advice(
            self,
            resume_text: str,
            target_role: Optional[str] = None,
            current_role: Optional[str] = None,
            job_matches: Optional[List[Dict]] = None
    ) -> Dict:
        """Generate comprehensive career advice using RAG approach"""
        logger.info(f"Generating career advice for target role: {target_role or 'General'}")

        # Analyze current skills and gaps
        current_skills = self._extract_skills_from_resume(resume_text)

        # Generate comprehensive advice using Claude
        advice = self._generate_advice_with_claude(
            resume_text=resume_text,
            current_role=current_role,
            target_role=target_role,
            current_skills=current_skills,
            job_matches=job_matches
        )

        # Generate learning path
        learning_path = self._generate_learning_path(
            current_skills=current_skills,
            target_role=target_role,
            skill_gaps=advice.get('skill_gaps', [])
        )

        # Generate career progression
        career_progression = self._generate_career_progression(
            current_role=current_role,
            target_role=target_role
        )

        return {
            "current_assessment": advice.get('assessment', ''),
            "skill_gaps": advice.get('skill_gaps', []),
            "learning_path": learning_path,
            "career_progression": career_progression,
            "market_insights": advice.get('market_insights', ''),
            "action_plan": advice.get('action_plan', [])
        }

    def _extract_skills_from_resume(self, resume_text: str) -> List[str]:
        """Extract skills from resume"""
        text_lower = resume_text.lower()
        found_skills = set()

        for skill in settings.TECH_SKILLS:
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(skill)

        return sorted(list(found_skills))

    def _generate_advice_with_claude(
            self,
            resume_text: str,
            current_role: Optional[str],
            target_role: Optional[str],
            current_skills: List[str],
            job_matches: Optional[List[Dict]]
    ) -> Dict:
        """Use Claude to generate personalized career advice"""

        # Prepare context from job matches
        job_context = ""
        if job_matches:
            top_matches = job_matches[:3]
            job_context = "\n".join([
                f"- {job['title']} at {job['company']} (Match: {job.get('match_score', 0)}%)"
                for job in top_matches
            ])

        prompt = f"""You are an expert career advisor providing personalized guidance.

**Candidate's Profile:**
Resume Summary: {resume_text[:1500]}
Current Role: {current_role or 'Entry-level / Career change'}
Target Role: {target_role or 'Software Engineer'}
Current Skills: {', '.join(current_skills) if current_skills else 'Limited technical skills'}

**Recent Job Matches:**
{job_context if job_context else 'No recent job matches'}

Provide comprehensive career advice in the following structure:

1. **Current Assessment** (2-3 sentences)
   - Evaluate their current skill level and market readiness
   - Highlight key strengths

2. **Critical Skill Gaps** (List 3-5 specific skills)
   - Identify the most important missing skills for their target role
   - Prioritize by market demand and career impact

3. **Market Insights** (2-3 sentences)
   - Current demand for their target role
   - Salary expectations for their skill level
   - Industry trends affecting their career path

4. **Action Plan** (4-6 specific, actionable steps)
   - Immediate actions (Week 1-2)
   - Short-term goals (Month 1-2)
   - Medium-term objectives (Month 3-6)
   - Each step should be specific and measurable

Be encouraging but realistic. Provide concrete, actionable advice."""

        try:
            response = self.client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=settings.MAX_TOKENS_CAREER_ADVICE,
                messages=[{"role": "user", "content": prompt}]
            )

            advice_text = response.content[0].text.strip()
            parsed_advice = self._parse_claude_response(advice_text, current_skills)
            return parsed_advice

        except Exception as e:
            logger.error(f"Error generating career advice: {str(e)}")
            return self._generate_fallback_advice(current_skills, target_role)

    def _parse_claude_response(self, response_text: str, current_skills: List[str]) -> Dict:
        """Parse Claude's structured response"""
        lines = response_text.split('\n')

        assessment = ""
        skill_gaps = []
        market_insights = ""
        action_plan = []

        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Identify sections (case-insensitive)
            line_lower = line.lower()
            if "current assessment" in line_lower or (line_lower.startswith("1.") and "assessment" in line_lower):
                current_section = "assessment"
                continue
            elif "skill gap" in line_lower or "critical skill" in line_lower or (
                    line_lower.startswith("2.") and "skill" in line_lower):
                current_section = "skills"
                continue
            elif "market insight" in line_lower or (line_lower.startswith("3.") and "market" in line_lower):
                current_section = "market"
                continue
            elif "action plan" in line_lower or (line_lower.startswith("4.") and "action" in line_lower):
                current_section = "actions"
                continue

            # Skip header markers
            if line.startswith(('**', '#', '###')):
                continue

            # Add content to current section
            if current_section == "assessment":
                if not line.startswith(('-', '•', '*')) and len(line) > 10:
                    assessment += line + " "
            elif current_section == "skills":
                if line.startswith(('-', '•', '*')) or (line[0].isdigit() and '.' in line[:3]):
                    skill_text = re.sub(r'^[-•*\d.)\s]+', '', line).strip()
                    if skill_text and len(skill_text) < 150:
                        skill_name = skill_text.split(':')[0].split('-')[0].strip()
                        skill_gaps.append({
                            "skill": skill_name,
                            "importance": "Critical",
                            "current_level": "Beginner" if any(
                                s.lower() in skill_name.lower() for s in current_skills) else "None",
                            "target_level": "Intermediate"
                        })
            elif current_section == "market":
                if not line.startswith(('-', '•', '*')) and len(line) > 10:
                    market_insights += line + " "
            elif current_section == "actions":
                if line.startswith(('-', '•', '*')) or (line[0].isdigit() and '.' in line[:3]):
                    action_text = re.sub(r'^[-•*\d.)\s]+', '', line).strip()
                    if action_text and len(action_text) > 5:
                        action_plan.append(action_text)

        return {
            "assessment": assessment.strip() or "Ready to advance your career with focused skill development.",
            "skill_gaps": skill_gaps[:5] if skill_gaps else [
                {"skill": "Advanced programming", "importance": "Critical", "current_level": "Beginner",
                 "target_level": "Intermediate"}
            ],
            "market_insights": market_insights.strip() or "Strong market demand for technical roles. Focus on building practical skills.",
            "action_plan": action_plan[:6] if action_plan else [
                "Build 2-3 portfolio projects",
                "Practice coding daily",
                "Network with professionals",
                "Apply to 5-10 relevant positions weekly"
            ]
        }

    def _generate_fallback_advice(self, current_skills: List[str], target_role: Optional[str]) -> Dict:
        """Generate fallback advice if Claude fails"""
        return {
            "assessment": f"You have {len(current_skills)} relevant technical skills. Focus on building a strong portfolio and gaining practical experience.",
            "skill_gaps": [
                {"skill": "Advanced programming", "importance": "Critical", "current_level": "Beginner",
                 "target_level": "Intermediate"},
                {"skill": "System design", "importance": "Important", "current_level": "None",
                 "target_level": "Beginner"},
                {"skill": "Cloud platforms", "importance": "Important", "current_level": "None",
                 "target_level": "Beginner"}
            ],
            "market_insights": f"The {target_role or 'software engineering'} market is competitive. Focus on building projects and networking.",
            "action_plan": [
                "Complete 2-3 personal projects demonstrating key skills",
                "Contribute to open source projects",
                "Build a professional online presence (GitHub, LinkedIn)",
                "Practice coding interviews daily",
                "Network with professionals in your target role"
            ]
        }

    def _generate_learning_path(
            self,
            current_skills: List[str],
            target_role: Optional[str],
            skill_gaps: List[Dict]
    ) -> List[Dict]:
        """Generate learning resource recommendations"""
        learning_resources = []

        # Extract missing skills
        missing_skills = [gap['skill'].lower() for gap in skill_gaps]

        # Generate recommendations for each missing skill
        for skill in missing_skills[:5]:
            resources = self._get_resources_for_skill(skill)
            learning_resources.extend(resources)

        return learning_resources[:10]  # Limit to 10 resources

    def _get_resources_for_skill(self, skill: str) -> List[Dict]:
        """Get learning resources for a specific skill"""
        skill_lower = skill.lower()

        # Skill-specific resource recommendations
        skill_resources = {
            "python": [
                {"title": "Python for Everybody", "type": "Course",
                 "url": "https://www.coursera.org/specializations/python", "duration": "4 months",
                 "difficulty": "Beginner"},
            ],
            "java": [
                {"title": "Java Programming Masterclass", "type": "Course",
                 "url": "https://www.udemy.com/course/java-the-complete-java-developer-course/",
                 "duration": "80 hours", "difficulty": "Beginner"},
            ],
            "javascript": [
                {"title": "JavaScript - The Complete Guide", "type": "Course",
                 "url": "https://www.udemy.com/course/javascript-the-complete-guide-2020-beginner-advanced/",
                 "duration": "50 hours", "difficulty": "Intermediate"},
            ],
            "machine learning": [
                {"title": "Machine Learning by Andrew Ng", "type": "Course",
                 "url": "https://www.coursera.org/learn/machine-learning", "duration": "11 weeks",
                 "difficulty": "Intermediate"},
            ],
            "docker": [
                {"title": "Docker for Developers", "type": "Course",
                 "url": "https://www.udemy.com/course/docker-kubernetes/", "duration": "6 hours",
                 "difficulty": "Beginner"},
            ],
            "react": [
                {"title": "React - The Complete Guide", "type": "Course",
                 "url": "https://www.udemy.com/course/react-the-complete-guide/", "duration": "40 hours",
                 "difficulty": "Intermediate"},
            ],
            "system design": [
                {"title": "System Design Interview Course", "type": "Course",
                 "url": "https://www.educative.io/courses/grokking-the-system-design-interview",
                 "duration": "8 weeks", "difficulty": "Advanced"},
            ],
            "cloud": [
                {"title": "AWS Certified Solutions Architect", "type": "Course",
                 "url": "https://www.udemy.com/course/aws-certified-solutions-architect-associate/",
                 "duration": "25 hours", "difficulty": "Intermediate"},
            ]
        }

        # Check for partial matches
        for key, resources in skill_resources.items():
            if key in skill_lower or skill_lower in key:
                return resources

        # Generic resource
        return [{
            "title": f"Learn {skill.title()}",
            "type": "Course",
            "url": f"https://www.coursera.org/search?query={skill.replace(' ', '+')}",
            "duration": "Varies",
            "difficulty": "Intermediate"
        }]

    def _generate_career_progression(
            self,
            current_role: Optional[str],
            target_role: Optional[str]
    ) -> List[Dict]:
        """Generate career progression path"""
        progressions = {
            "junior": [
                {
                    "role": "Junior Developer",
                    "timeline": "Current - 2 years",
                    "key_skills_needed": ["Basic programming", "Version control", "Testing"],
                    "typical_responsibilities": ["Write code under supervision", "Fix bugs", "Learn best practices"]
                },
                {
                    "role": "Mid-level Developer",
                    "timeline": "2-4 years",
                    "key_skills_needed": ["System design basics", "Code review", "Mentoring"],
                    "typical_responsibilities": ["Own features end-to-end", "Code reviews", "Technical decisions"]
                },
                {
                    "role": "Senior Developer",
                    "timeline": "5+ years",
                    "key_skills_needed": ["Architecture", "Leadership", "Cross-team collaboration"],
                    "typical_responsibilities": ["Design systems", "Mentor team", "Strategic planning"]
                }
            ],
            "default": [
                {
                    "role": "Entry Level",
                    "timeline": "0-2 years",
                    "key_skills_needed": ["Core technical skills", "Communication", "Problem-solving"],
                    "typical_responsibilities": ["Learn and contribute", "Complete assigned tasks", "Build foundation"]
                },
                {
                    "role": "Intermediate Level",
                    "timeline": "2-5 years",
                    "key_skills_needed": ["Advanced technical skills", "Project ownership", "Collaboration"],
                    "typical_responsibilities": ["Lead small projects", "Mentor juniors", "Drive initiatives"]
                },
                {
                    "role": "Senior Level",
                    "timeline": "5+ years",
                    "key_skills_needed": ["Expertise", "Strategy", "Leadership"],
                    "typical_responsibilities": ["Define architecture", "Guide team direction", "Business impact"]
                }
            ]
        }

        # Determine which progression to use
        if current_role and "junior" in current_role.lower():
            return progressions["junior"]
        else:
            return progressions["default"]


# Singleton instance
try:
    career_advisor = CareerAdvisor()
except Exception as e:
    logger.error(f"Failed to initialize CareerAdvisor: {str(e)}")
    career_advisor = None