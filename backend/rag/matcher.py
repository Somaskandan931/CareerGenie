from typing import List, Dict, Any
import anthropic
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger( __name__ )


class RAGJobMatcher :
    """
    RAG-based job matcher using retrieved jobs and LLM reasoning
    """

    def __init__ ( self ) :
        self.api_key = os.getenv( "ANTHROPIC_API_KEY" )
        if not self.api_key :
            logger.warning( "ANTHROPIC_API_KEY not set - using fallback scoring" )
        self.client = anthropic.Anthropic( api_key=self.api_key ) if self.api_key else None

    def _extract_resume_skills ( self, resume_text: str ) -> List[str] :
        """Extract skills from resume text using simple pattern matching"""
        common_skills = [
            'python', 'java', 'javascript', 'typescript', 'react', 'node', 'sql',
            'machine learning', 'ml', 'deep learning', 'nlp', 'computer vision',
            'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'git',
            'spring boot', 'django', 'flask', 'fastapi', 'express',
            'mongodb', 'postgresql', 'mysql', 'redis', 'kafka',
            'data analysis', 'statistics', 'r', 'tableau', 'powerbi'
        ]

        resume_lower = resume_text.lower()
        found_skills = [skill for skill in common_skills if skill in resume_lower]
        return found_skills

    def _calculate_skill_match ( self, resume_skills: List[str], job_skills: List[str] ) -> float :
        """
        Calculate skill overlap score

        Returns:
            Score between 0-100
        """
        if not job_skills :
            return 0.0

        resume_skills_lower = [s.lower() for s in resume_skills]
        job_skills_lower = [s.lower() for s in job_skills]

        matched = sum( 1 for skill in job_skills_lower if skill in resume_skills_lower )
        return (matched / len( job_skills_lower )) * 100

    def generate_explanation (
            self,
            resume_text: str,
            job: Dict[str, Any],
            match_score: float
    ) -> Dict[str, Any] :
        """
        Generate explainable match reasoning using RAG

        Args:
            resume_text: Full resume text
            job: Retrieved job posting
            match_score: Calculated match score

        Returns:
            Dict with matched_skills, missing_skills, explanation, and recommendation
        """
        resume_skills = self._extract_resume_skills( resume_text )
        job_skills_required = job['skills_required']
        job_skills_preferred = job.get( 'skills_preferred', [] )

        # Calculate matches
        matched_skills = [
            skill for skill in job_skills_required
            if skill.lower() in [s.lower() for s in resume_skills]
        ]

        missing_required = [
            skill for skill in job_skills_required
            if skill.lower() not in [s.lower() for s in resume_skills]
        ]

        missing_preferred = [
            skill for skill in job_skills_preferred
            if skill.lower() not in [s.lower() for s in resume_skills]
        ]

        # Generate LLM explanation if API available
        if self.client :
            try :
                explanation = self._generate_llm_explanation(
                    resume_text, job, matched_skills, missing_required, missing_preferred
                )
            except Exception as e :
                logger.error( f"LLM explanation failed: {e}" )
                explanation = self._generate_fallback_explanation(
                    matched_skills, missing_required, match_score
                )
        else :
            explanation = self._generate_fallback_explanation(
                matched_skills, missing_required, match_score
            )

        return {
            "matched_skills" : matched_skills,
            "missing_required_skills" : missing_required,
            "missing_preferred_skills" : missing_preferred,
            "explanation" : explanation,
            "recommendation" : self._generate_recommendation( match_score )
        }

    def _generate_llm_explanation (
            self,
            resume_text: str,
            job: Dict[str, Any],
            matched_skills: List[str],
            missing_required: List[str],
            missing_preferred: List[str]
    ) -> str :
        """Generate explanation using Claude with RAG"""

        prompt = f"""You are an expert career advisor analyzing job fit based on RETRIEVED job posting data.

RETRIEVED JOB POSTING:
Title: {job['title']}
Company: {job['company']}
Description: {job['job_description']}

CANDIDATE RESUME EXTRACT:
{resume_text[:1500]}

ANALYSIS RESULTS:
- Matched Required Skills: {', '.join( matched_skills ) if matched_skills else 'None'}
- Missing Required Skills: {', '.join( missing_required ) if missing_required else 'None'}
- Missing Preferred Skills: {', '.join( missing_preferred ) if missing_preferred else 'None'}

INSTRUCTIONS:
1. Explain why this job matches or doesn't match based ONLY on the retrieved job description above
2. Cite specific requirements from the job posting
3. Be honest about skill gaps
4. Keep explanation under 150 words
5. Use evidence-based reasoning

Provide a concise, actionable explanation:"""

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[{"role" : "user", "content" : prompt}]
        )

        return message.content[0].text.strip()

    def _generate_fallback_explanation (
            self,
            matched_skills: List[str],
            missing_required: List[str],
            match_score: float
    ) -> str :
        """Generate rule-based explanation when LLM unavailable"""

        if match_score >= 70 :
            tone = "Strong match"
        elif match_score >= 50 :
            tone = "Moderate match"
        else :
            tone = "Weak match"

        explanation = f"{tone} based on skill analysis. "

        if matched_skills :
            explanation += f"You have {len( matched_skills )} required skills: {', '.join( matched_skills[:3] )}. "

        if missing_required :
            explanation += f"Missing {len( missing_required )} required skills: {', '.join( missing_required[:3] )}. "

        if match_score >= 60 :
            explanation += "Consider applying and highlighting your matching skills."
        elif missing_required :
            explanation += "Consider upskilling in missing areas before applying."

        return explanation

    def _generate_recommendation ( self, match_score: float ) -> str :
        """Generate application recommendation"""
        if match_score >= 75 :
            return "Highly Recommended - Strong fit, apply immediately"
        elif match_score >= 60 :
            return "Recommended - Good fit with minor gaps"
        elif match_score >= 45 :
            return "Consider - Requires upskilling in key areas"
        else :
            return "Not Recommended - Significant skill gaps"

    def match_jobs (
            self,
            resume_text: str,
            retrieved_jobs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]] :
        """
        Process retrieved jobs and generate explainable matches

        Args:
            resume_text: Full resume text
            retrieved_jobs: Jobs from vector store

        Returns:
            Jobs with match scores, explanations, and recommendations
        """
        resume_skills = self._extract_resume_skills( resume_text )
        results = []

        for job in retrieved_jobs :
            # Calculate comprehensive match score
            skill_score = self._calculate_skill_match(
                resume_skills,
                job['skills_required']
            )

            semantic_score = job['similarity_score']

            # Weighted final score (60% skills, 40% semantic)
            final_score = (0.6 * skill_score) + (0.4 * semantic_score)

            # Generate explanation
            analysis = self.generate_explanation( resume_text, job, final_score )

            results.append( {
                "job_id" : job['job_id'],
                "title" : job['title'],
                "company" : job['company'],
                "location" : job['location'],
                "employment_type" : job['employment_type'],
                "salary_range" : job['salary_range'],
                "apply_link" : job['apply_link'],
                "match_score" : round( final_score, 2 ),
                "skill_match_score" : round( skill_score, 2 ),
                "semantic_match_score" : round( semantic_score, 2 ),
                "matched_skills" : analysis['matched_skills'],
                "missing_required_skills" : analysis['missing_required_skills'],
                "missing_preferred_skills" : analysis['missing_preferred_skills'],
                "explanation" : analysis['explanation'],
                "recommendation" : analysis['recommendation']
            } )

        # Sort by final match score
        results.sort( key=lambda x : x['match_score'], reverse=True )

        return results