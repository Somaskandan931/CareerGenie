from groq import Groq
from typing import List, Dict
import logging
import re
from datetime import datetime

from backend.config import settings
from backend.services.vector_store import vector_store

logger = logging.getLogger( __name__ )


class JobMatcher :
    def __init__ ( self ) :
        """Initialize Groq client"""
        if not settings.GROQ_API_KEY :
            raise ValueError( "GROQ_API_KEY not configured" )

        self.client = Groq( api_key=settings.GROQ_API_KEY )

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

        # Critical skills for penalty calculation
        self.critical_skills = ["python", "java", "javascript", "sql", "aws", "react", "docker"]

    def match_resume_to_jobs ( self, resume_text: str, top_k: int = 10,
                               force_refresh: bool = False,
                               location: str = "India" ) -> List[Dict] :
        """
        Match resume to jobs using RAG + Groq

        Process:
        1. Fetch fresh jobs from scraper (optional)
        2. Semantic search (RAG retrieval)
        3. Skill extraction
        4. Groq LLM explanation
        5. Score calculation
        """
        logger.info( f"Matching resume to top {top_k} jobs..." )

        # Optionally refresh jobs from scraper
        if force_refresh or vector_store.get_stats()["total_jobs"] < 20 :
            try :
                from backend.services.job_scraper import get_job_scraper
                scraper = get_job_scraper()

                # Extract target role from resume or use default
                target_role = self._extract_target_role( resume_text )

                # Fetch fresh jobs
                fresh_jobs = scraper.fetch_jobs(
                    query=target_role,
                    location=location,
                    num_jobs=50
                )

                # Index them
                if fresh_jobs :
                    # Clear old jobs if force refresh
                    if force_refresh :
                        vector_store.clear()
                    vector_store.index_jobs( fresh_jobs )
                    logger.info( f"Refreshed with {len( fresh_jobs )} fresh jobs" )
            except Exception as e :
                logger.error( f"Failed to refresh jobs: {e}" )

        # Step 1: RAG Retrieval
        retrieved_jobs = vector_store.search( resume_text, top_k=top_k * 2 )  # Get more for filtering

        if not retrieved_jobs :
            logger.warning( "No jobs found in vector store" )
            return []

        # Step 2: Extract skills
        resume_skills = self._extract_skills( resume_text )
        logger.info( f"Extracted {len( resume_skills )} skills from resume" )

        matches = []

        for job in retrieved_jobs :
            job_skills = self._extract_skills( job['description'] )

            matched_skills = list( set( resume_skills ) & set( job_skills ) )
            missing_skills = list( set( job_skills ) - set( resume_skills ) )

            # Calculate match score with improved algorithm
            match_score = self._calculate_score(
                matched_skills,
                missing_skills,
                job.get( 'distance', 0.5 ),
                job['title'],
                resume_text
            )

            # Skip low matches
            if match_score < 30 :
                continue

            # Step 3: LLM Explanation (only for top matches)
            explanation = ""
            if match_score > 50 :
                explanation = self._generate_explanation(
                    resume_text,
                    job['title'],
                    job['company'],
                    job['description'],
                    matched_skills,
                    missing_skills
                )

            recommendation = self._get_recommendation( match_score )

            matches.append( {
                "job_id" : job['id'],
                "title" : job['title'],
                "company" : job['company'],
                "location" : job['location'],
                "match_score" : round( match_score, 1 ),
                "matched_skills" : matched_skills[:8],  # Limit display
                "missing_skills" : missing_skills[:5],
                "explanation" : explanation,
                "recommendation" : recommendation,
                "apply_link" : job.get( 'apply_link', '' ),
                "fetched_at" : job.get( 'fetched_at', datetime.now().isoformat() )
            } )

        # Sort by match score and limit to top_k
        matches.sort( key=lambda x : x['match_score'], reverse=True )
        matches = matches[:top_k]

        logger.info( f"Generated {len( matches )} job matches" )
        return matches

    def _extract_target_role ( self, resume_text: str ) -> str :
        """Extract target role from resume or use default"""
        # Common roles to look for
        common_roles = [
            "software engineer", "data scientist", "machine learning engineer",
            "web developer", "devops engineer", "product manager", "data analyst",
            "frontend developer", "backend developer", "full stack developer",
            "cloud engineer", "site reliability engineer", "sre"
        ]

        text_lower = resume_text.lower()

        # Look for explicit target in resume
        for role in common_roles :
            if role in text_lower :
                return role

        # Check for job titles in current role
        current_role_match = re.search( r'current role[:\s]+([a-z\s]+)', text_lower )
        if current_role_match :
            return current_role_match.group( 1 ).strip()

        return "software engineer"  # default

    def _extract_skills ( self, text: str ) -> List[str] :
        """Extract technical skills using regex"""
        text_lower = text.lower()
        skills = set()

        for pattern in self.skill_patterns :
            matches = re.findall( pattern, text_lower, re.IGNORECASE )
            for match in matches :
                # Handle tuples from regex groups
                if isinstance( match, tuple ) :
                    skills.update( [m for m in match if m] )
                else :
                    skills.add( match.lower() )

        return sorted( list( skills ) )

    def _calculate_score ( self, matched_skills: List[str], missing_skills: List[str],
                           semantic_distance: float, job_title: str = "",
                           resume_text: str = "" ) -> float :
        """Calculate more accurate match score"""

        # 1. Semantic similarity (vector search) - 35% weight
        semantic_score = max( 0, 35 * (1 - min( semantic_distance, 1.0 )) )

        # 2. Skills match - 45% weight
        total_skills = len( matched_skills ) + len( missing_skills )
        if total_skills > 0 :
            # Weight by skill importance
            skills_ratio = len( matched_skills ) / total_skills
            skills_score = 45 * skills_ratio
        else :
            skills_score = 22.5  # Default if no skills extracted (half of 45)

        # 3. Title/role match - 20% weight
        title_score = self._calculate_title_match( resume_text, job_title )

        # Calculate total
        total_score = semantic_score + skills_score + title_score

        # Apply penalties for critical missing skills
        critical_missing = [s for s in missing_skills if s.lower() in self.critical_skills]
        penalty = min( 15, len( critical_missing ) * 5 )

        total_score = max( 0, min( 100, total_score - penalty ) )

        return round( total_score, 1 )

    def _calculate_title_match ( self, resume_text: str, job_title: str ) -> float :
        """Calculate how well job title matches resume"""
        resume_lower = resume_text.lower()
        title_lower = job_title.lower()

        # Extract key terms from job title
        title_words = set( re.findall( r'\b[a-z]+\b', title_lower ) )

        # Common variations mapping
        variations = {
            "engineer" : ["engineer", "developer", "programmer", "architect"],
            "developer" : ["developer", "engineer", "programmer", "coder"],
            "senior" : ["senior", "lead", "principal", "staff"],
            "junior" : ["junior", "entry", "fresher", "graduate"],
            "data" : ["data", "analytics", "analyst", "scientist"],
            "cloud" : ["cloud", "aws", "azure", "gcp"],
            "frontend" : ["frontend", "front-end", "ui", "react", "vue", "angular"],
            "backend" : ["backend", "back-end", "api", "server"],
            "fullstack" : ["fullstack", "full-stack", "full stack"],
        }

        score = 0
        matched_terms = set()

        for word in title_words :
            if word in resume_lower :
                score += 4
                matched_terms.add( word )
            elif word in variations :
                for variant in variations[word] :
                    if variant in resume_lower and variant not in matched_terms :
                        score += 2
                        matched_terms.add( variant )
                        break

        return min( 20, score )  # Max 20 points

    def _get_recommendation ( self, score: float ) -> str :
        """Recommendation label"""
        if score >= 80 :
            return "Excellent Match"
        elif score >= 65 :
            return "Strong Match"
        elif score >= 50 :
            return "Good Match"
        elif score >= 35 :
            return "Moderate Match"
        else :
            return "Weak Match"

    def _generate_explanation ( self, resume_text: str, job_title: str,
                                job_company: str, job_description: str,
                                matched_skills: List[str], missing_skills: List[str] ) -> str :
        """Generate explanation using Groq LLM"""

        resume_preview = resume_text[:1500]
        job_desc_preview = job_description[:1500]

        prompt = f"""You are an expert career advisor analyzing a job match.

Resume Summary:
{resume_preview}

Job Position: {job_title} at {job_company}
Job Description:
{job_desc_preview}

Matched Skills: {', '.join( matched_skills ) if matched_skills else 'None identified'}
Missing Skills: {', '.join( missing_skills[:3] ) if missing_skills else 'None identified'}

Provide a brief, actionable 2-3 sentence explanation:
1. What makes this a good/weak match
2. One specific gap to address
3. Final recommendation (apply/practice/prepare)
"""

        try :
            response = self.client.chat.completions.create(
                model=settings.GROQ_CHAT_MODEL,
                messages=[
                    {"role" : "system", "content" : "You are an expert career advisor."},
                    {"role" : "user", "content" : prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e :
            logger.error( f"Error generating explanation: {str( e )}" )
            if matched_skills :
                return f"Good match based on {len( matched_skills )} aligned skills. {'Focus on ' + missing_skills[0] if missing_skills else 'Ready to apply!'}"
            else :
                return f"Consider building skills in {missing_skills[0] if missing_skills else 'key areas'} before applying."


# Singleton instance
_job_matcher = None


def get_job_matcher () :
    global _job_matcher
    if _job_matcher is None :
        _job_matcher = JobMatcher()
    return _job_matcher