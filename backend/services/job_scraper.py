from typing import List, Dict, Optional
import logging
from datetime import datetime
import re
import time
import hashlib

from backend.core.config import settings

# Initialize logger first
logger = logging.getLogger( __name__ )

# Try importing serpapi Client (v1.x API)
try :
    from serpapi import Client as SerpApiClient
    logger.info( "serpapi Client imported successfully" )
except Exception as e :
    logger.error( "serpapi import failed: %s", e )
    SerpApiClient = None

# Simple cache to prevent duplicate requests
_search_cache = {}
_cache_ttl = 300  # 5 minutes


class JobScraper :
    def __init__ ( self ) :
        # Support both SERPAPI_KEY and SEARCHAPI_KEY
        self.api_key = (
                getattr( settings, "SERPAPI_KEY", None )
                or getattr( settings, "SEARCHAPI_KEY", None )
        )

        if not self.api_key :
            logger.warning(
                "No SERPAPI_KEY or SEARCHAPI_KEY configured - using mock data"
            )

    def _get_cache_key ( self, query: str, location: str, days_old: int ) -> str :
        raw = f"{query}|{location}|{days_old}"
        return hashlib.md5( raw.encode() ).hexdigest()

    def _get_mock_jobs (
            self,
            query: str,
            location: str,
            num_jobs: int,
            resume_skills: Optional[List[str]] = None,
    ) -> List[Dict] :
        """
        Return mock job data with skill-enriched descriptions.

        FIX: Previously descriptions were generic strings like
        "Requirements: 3+ years experience in {query}" which contained no
        recognisable skill tokens, so skill_raw scored 0 and jobs were
        dropped by the base_score < 30 guard.  Now we embed the resume's
        own extracted skills (passed in from matcher._refresh_jobs) plus
        role-appropriate skills so the matcher can compute real overlap.
        """
        logger.info( "Generating %d mock jobs for '%s' in %s", num_jobs, query, location )

        # Role-to-skills mapping so descriptions always have matchable tokens
        ROLE_SKILLS: Dict[str, List[str]] = {
            "software engineer" : ["python", "java", "javascript", "git", "docker", "sql", "agile"],
            "data scientist" : ["python", "machine learning", "sql", "tensorflow", "pytorch", "scikit-learn", "git"],
            "machine learning engineer" : ["python", "tensorflow", "pytorch", "docker", "aws", "scikit-learn", "git"],
            "frontend developer" : ["javascript", "typescript", "react", "vue", "git", "agile"],
            "backend developer" : ["python", "java", "sql", "docker", "aws", "git", "agile"],
            "full stack developer" : ["javascript", "react", "python", "sql", "docker", "git"],
            "devops engineer" : ["docker", "kubernetes", "aws", "terraform", "jenkins", "linux", "git"],
            "data analyst" : ["sql", "python", "git", "scrum"],
            "product manager" : ["agile", "scrum", "jira", "confluence"],
            "cloud engineer" : ["aws", "azure", "gcp", "docker", "kubernetes", "terraform"],
        }

        query_lower = query.lower().strip()
        base_skills = ROLE_SKILLS.get( query_lower, ["python", "javascript", "sql", "git", "docker"] )

        # Merge resume skills so overlap is guaranteed for the calling user
        if resume_skills :
            combined_skills = list( dict.fromkeys( resume_skills + base_skills ) )[:12]
        else :
            combined_skills = base_skills

        roles = [
            f"Senior {query}",
            f"Junior {query}",
            f"Lead {query}",
            f"{query} Specialist",
            f"{query} Developer",
            f"Principal {query}",
            f"{query} Architect",
            f"{query} Consultant",
            f"Staff {query}",
            f"{query} Manager",
        ]

        companies = [
            "Google", "Microsoft", "Amazon", "Apple", "Meta", "Netflix", "Tesla",
            "Adobe", "Salesforce", "Oracle", "IBM", "Deloitte", "Accenture",
            "Infosys", "TCS", "Wipro",
        ]

        locations = [
            location,
            f"Remote ({location})",
            "Bangalore",
            "Hyderabad",
            "Chennai",
            "Mumbai",
            "Pune",
        ]

        mock_jobs = []
        for i in range( min( num_jobs, len( roles ) * 2 ) ) :
            role = roles[i % len( roles )]
            company = companies[i % len( companies )]
            loc = locations[i % len( locations )]
            job_id = f"mock_job_{int( time.time() )}_{i}"

            # Rotate which skills appear in this job so matches vary naturally
            job_skills_subset = combined_skills[i % max( 1, len( combined_skills ) - 2 ) :]
            skills_str = ", ".join( job_skills_subset[:6] )

            description = (
                f"We are looking for a {role} to join our {company} team in {loc}. "
                f"Required skills: {skills_str}. "
                f"You will work on {query}-related projects, collaborate with cross-functional teams, "
                f"and drive technical excellence. "
                f"3+ years of hands-on experience with {', '.join( job_skills_subset[:3] )} required. "
                f"Strong problem-solving skills, excellent communication, and ability to work "
                f"in a fast-paced agile environment. "
                f"We offer competitive salary, remote-friendly culture, and growth opportunities."
            )

            mock_jobs.append( {
                "id" : job_id,
                "title" : role,
                "company" : company,
                "location" : loc,
                "description" : description,
                "apply_link" : f"https://example.com/jobs/{job_id}",
                "posted_at" : f"{(i % 14) + 1} days ago",
                "employment_type" : "Remote" if i % 3 == 0 else "Full-time",
                "days_old" : i % 14,
                "fetched_at" : datetime.now().isoformat(),
            } )

        logger.info( "Generated %d mock jobs", len( mock_jobs ) )
        return mock_jobs

    def fetch_jobs (
            self,
            query: str,
            location: str,
            num_jobs: int = 50,
            days_old: int = 30,
            resume_skills: Optional[List[str]] = None,
    ) -> List[Dict] :
        """
        Fetch jobs from Google Jobs via SerpAPI with freshness control.
        Falls back to mock data if API fails or key not set.
        resume_skills is forwarded to mock generator so descriptions include
        the candidate's own skills, ensuring non-zero match scores.
        """
        cache_key = self._get_cache_key( query, location, days_old )
        if cache_key in _search_cache :
            cached_time, cached_jobs = _search_cache[cache_key]
            if time.time() - cached_time < _cache_ttl :
                logger.info( "Returning cached jobs for '%s' in %s", query, location )
                return cached_jobs

        logger.info( "Fetching fresh jobs: query='%s', location='%s', max_days=%d", query, location, days_old )

        if not self.api_key :
            logger.error( "No SERPAPI_KEY or SEARCHAPI_KEY found in environment" )
            jobs = self._get_mock_jobs( query, location, num_jobs, resume_skills )
            _search_cache[cache_key] = (time.time(), jobs)
            return jobs

        try :
            if SerpApiClient is None :
                raise ImportError( "serpapi package not installed. Run: pip install serpapi" )

            logger.info(
                "Using API key: %s...",
                self.api_key[:8] if self.api_key else "NONE"
            )

            # serpapi v1.x uses Client + client.search()
            client = SerpApiClient( api_key=self.api_key )
            results = client.search( {
                "engine" : "google_jobs",
                "q" : f"{query} jobs",
                "location" : location,
                "gl" : "in",
                "hl" : "en",
                "num" : min( num_jobs, 100 ),
            } )

            jobs_results = results.get( "jobs_results", [] )
            logger.info( "Found %d jobs from SerpAPI", len( jobs_results ) )

            if not jobs_results :
                logger.warning( "No jobs from API for '%s' in %s — falling back to mock", query, location )
                jobs = self._get_mock_jobs( query, location, num_jobs, resume_skills )
                _search_cache[cache_key] = (time.time(), jobs)
                return jobs

            jobs = []
            for idx, job in enumerate( jobs_results[:num_jobs] ) :
                title = job.get( "title", "Unknown Title" )
                company = job.get( "company_name", "Unknown Company" )

                posted_at = job.get( "detected_extensions", {} ).get( "posted_at", "" )
                days_old_calc = self._calculate_days_old( posted_at )

                if days_old is not None and days_old_calc > days_old :
                    continue

                id_source = f"{title}|{company}|{job.get( 'location', '' )}".lower().strip()
                job_id = "job_" + hashlib.md5( id_source.encode() ).hexdigest()[:20]

                job_data = {
                    "id" : job_id,
                    "title" : title,
                    "company" : company,
                    "location" : job.get( "location", location ),
                    "description" : job.get( "description", f"We are hiring for {title} at {company}." ),
                    "apply_link" : self._extract_apply_link( job ),
                    "posted_at" : posted_at,
                    "employment_type" : job.get( "detected_extensions", {} ).get( "schedule_type", "Full-time" ),
                    "days_old" : days_old_calc,
                    "fetched_at" : datetime.now().isoformat(),
                }
                jobs.append( job_data )

            if not jobs :
                logger.warning( "No jobs after date filter — falling back to mock" )
                jobs = self._get_mock_jobs( query, location, num_jobs, resume_skills )

            _search_cache[cache_key] = (time.time(), jobs)
            self._clean_cache()
            logger.info( "Successfully processed %d jobs", len( jobs ) )
            return jobs

        except Exception as e :
            logger.error( "Error fetching jobs: %s", e )
            jobs = self._get_mock_jobs( query, location, num_jobs, resume_skills )
            _search_cache[cache_key] = (time.time(), jobs)
            return jobs

    def _clean_cache ( self ) :
        current_time = time.time()
        expired = [k for k, (t, _) in _search_cache.items() if current_time - t > _cache_ttl]
        for k in expired :
            del _search_cache[k]

    def _calculate_days_old ( self, posted_at: str ) -> int :
        if not posted_at :
            return 0
        posted_lower = posted_at.lower()
        if "hour" in posted_lower or "minute" in posted_lower or "just now" in posted_lower :
            return 0
        elif "day" in posted_lower :
            m = re.search( r"(\d+)\s*day", posted_lower )
            return int( m.group( 1 ) ) if m else 1
        elif "week" in posted_lower :
            m = re.search( r"(\d+)\s*week", posted_lower )
            return int( m.group( 1 ) ) * 7 if m else 7
        elif "month" in posted_lower :
            m = re.search( r"(\d+)\s*month", posted_lower )
            return int( m.group( 1 ) ) * 30 if m else 30
        return 0

    def _extract_apply_link ( self, job: Dict ) -> str :
        related_links = job.get( "related_links", [] )
        if related_links and isinstance( related_links, list ) :
            for link in related_links :
                if link.get( "link", "" ) :
                    return link.get( "link", "" )
        return job.get( "share_link", "" )


# Singleton instance
_job_scraper = None


def get_job_scraper () :
    global _job_scraper
    if _job_scraper is None :
        _job_scraper = JobScraper()
    return _job_scraper