from groq import Groq
from typing import List, Dict
import logging
import re

from backend.config import settings
from backend.services.vector_store import vector_store

logger = logging.getLogger(__name__)


class JobMatcher:
    def __init__(self):
        """Initialize Groq client"""
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not configured")

        self.client = Groq(api_key=settings.GROQ_API_KEY)

        # Common tech skills for matching
        self.skill_patterns = [
            # Programming Languages
            r'\b(python|java|javascript|typescript|c\+\+|c#|ruby|go|rust|php|swift|kotlin)\b',
            # Frameworks
            r'\b(react|angular|vue|django|flask|fastapi|spring|express|node\.?js)\b',
            # Databases
            r'\b(sql|mysql|postgresql|mongodb|redis|dynamodb|oracle)\b',
            # Cloud & DevOps
            r'\b(aws|azure|gcp|docker|kubernetes|jenkins|terraform|ansible)\b',
            # AI/ML
            r'\b(machine learning|deep learning|tensorflow|pytorch|scikit-learn|nlp|computer vision)\b',
            # Tools
            r'\b(git|jira|confluence|linux|agile|scrum)\b'
        ]

    def match_resume_to_jobs(self, resume_text: str, top_k: int = 10) -> List[Dict]:
        """
        Match resume to jobs using RAG + Groq

        Process:
        1. Semantic search (RAG retrieval)
        2. Skill extraction
        3. Groq LLM explanation (RAG generation)
        4. Score calculation
        """
        logger.info(f"Matching resume to top {top_k} jobs...")

        # Step 1: RAG Retrieval
        retrieved_jobs = vector_store.search(resume_text, top_k=top_k)

        if not retrieved_jobs:
            logger.warning("No jobs found in vector store")
            return []

        # Step 2: Extract skills
        resume_skills = self._extract_skills(resume_text)
        logger.info(f"Extracted {len(resume_skills)} skills from resume")

        matches = []

        for job in retrieved_jobs:
            job_skills = self._extract_skills(job['description'])

            matched_skills = list(set(resume_skills) & set(job_skills))
            missing_skills = list(set(job_skills) - set(resume_skills))

            # Step 3: LLM Explanation (Groq)
            explanation = self._generate_explanation(
                resume_text,
                job['title'],
                job['company'],
                job['description'],
                matched_skills,
                missing_skills
            )

            # Step 4: Score
            match_score = self._calculate_score(
                matched_skills,
                missing_skills,
                job.get('distance', 0.5)
            )

            recommendation = self._get_recommendation(match_score)

            matches.append({
                "job_id": job['id'],
                "title": job['title'],
                "company": job['company'],
                "location": job['location'],
                "match_score": round(match_score, 1),
                "matched_skills": matched_skills,
                "missing_skills": missing_skills[:5],
                "explanation": explanation,
                "recommendation": recommendation,
                "apply_link": job.get('apply_link', '')
            })

        matches.sort(key=lambda x: x['match_score'], reverse=True)

        logger.info(f"Generated {len(matches)} job matches")
        return matches

    def _extract_skills(self, text: str) -> List[str]:
        """Extract technical skills using regex"""
        text_lower = text.lower()
        skills = set()

        for pattern in self.skill_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            skills.update(matches)

        return sorted(list(skills))

    def _calculate_score(self, matched_skills: List[str], missing_skills: List[str],
                         semantic_distance: float) -> float:
        """Calculate match score"""

        semantic_score = max(0, 50 * (1 - semantic_distance))
        matched_score = min(40, len(matched_skills) * 5)
        missing_penalty = min(20, len(missing_skills) * 2)

        total_score = semantic_score + matched_score - missing_penalty

        return max(0, min(100, total_score))

    def _get_recommendation(self, score: float) -> str:
        """Recommendation label"""
        if score >= 80:
            return "Excellent Match"
        elif score >= 65:
            return "Strong Match"
        elif score >= 50:
            return "Good Match"
        elif score >= 35:
            return "Moderate Match"
        else:
            return "Weak Match"

    def _generate_explanation(self, resume_text: str, job_title: str,
                              job_company: str, job_description: str,
                              matched_skills: List[str], missing_skills: List[str]) -> str:
        """Generate explanation using Groq LLM"""

        resume_preview = resume_text[:1500]
        job_desc_preview = job_description[:1500]

        prompt = f"""You are an expert career advisor analyzing a job match.

Resume Summary:
{resume_preview}

Job Position: {job_title} at {job_company}
Job Description:
{job_desc_preview}

Matched Skills: {', '.join(matched_skills) if matched_skills else 'None identified'}
Missing Skills: {', '.join(missing_skills[:3]) if missing_skills else 'None identified'}

Provide a brief, actionable 2-3 sentence explanation:
1. Strengths
2. One gap
3. Final recommendation
"""

        try:
            response = self.client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "You are an expert career advisor."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error generating explanation: {str(e)}")
            return f"Match based on {len(matched_skills)} aligned skills. Improve {missing_skills[0] if missing_skills else 'additional'} skills."


# Singleton instance
_job_matcher = None


def get_job_matcher():
    global _job_matcher
    if _job_matcher is None:
        _job_matcher = JobMatcher()
    return _job_matcher