from typing import List, Dict
from serpapi import GoogleSearch
import logging
from datetime import datetime
import re
import time
import hashlib

from backend.config import settings

logger = logging.getLogger( __name__ )

# Simple cache to prevent duplicate requests
_search_cache = {}
_cache_ttl = 300  # 5 minutes


class JobScraper :
    def __init__ ( self ) :
        if not settings.SERPAPI_KEY :
            logger.warning( "SERPAPI_KEY not configured - will use mock data" )
            self.api_key = None
        else :
            self.api_key = settings.SERPAPI_KEY

    def _get_cache_key ( self, query: str, location: str, days_old: int ) -> str :
        """Generate cache key for search query"""
        raw = f"{query}|{location}|{days_old}"
        return hashlib.md5( raw.encode() ).hexdigest()

    def _get_mock_jobs ( self, query: str, location: str, num_jobs: int ) -> List[Dict] :
        """Return mock job data when API fails or not configured"""
        logger.info( f"Generating {num_jobs} mock jobs for {query} in {location}" )

        mock_jobs = []
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
            f"{query} Manager"
        ]

        companies = ["Google", "Microsoft", "Amazon", "Apple", "Meta", "Netflix", "Tesla", "Adobe",
                     "Salesforce", "Oracle", "IBM", "Deloitte", "Accenture", "Infosys", "TCS", "Wipro"]

        locations = [location, f"Remote ({location})", f"Bangalore", f"Hyderabad", f"Chennai", f"Mumbai", f"Pune"]

        for i in range( min( num_jobs, len( roles ) * 2 ) ) :
            role_idx = i % len( roles )
            company_idx = i % len( companies )
            location_idx = i % len( locations )

            job_id = f"mock_job_{int( time.time() )}_{i}"
            days_old_val = i % 14

            mock_jobs.append( {
                "id" : job_id,
                "title" : roles[role_idx],
                "company" : companies[company_idx],
                "location" : locations[location_idx],
                "description" : f"We are looking for a {roles[role_idx]} to join our {companies[company_idx]} team. "
                                f"Requirements: 3+ years experience in {query}, strong problem-solving skills, "
                                f"excellent communication, and ability to work in a fast-paced environment. "
                                f"We offer competitive salary, benefits, and growth opportunities.",
                "apply_link" : f"https://example.com/jobs/{job_id}",
                "posted_at" : f"{days_old_val + 1} days ago",
                "employment_type" : "Full-time" if i % 3 != 0 else "Remote",
                "days_old" : days_old_val,
                "fetched_at" : datetime.now().isoformat(),
            } )

        logger.info( f"Generated {len( mock_jobs )} mock jobs" )
        return mock_jobs

    def fetch_jobs ( self, query: str, location: str, num_jobs: int = 50,
                     days_old: int = 7 ) -> List[Dict] :
        """
        Fetch jobs from Google Jobs via SerpAPI with freshness control
        Falls back to mock data if API fails
        """
        # Check cache first
        cache_key = self._get_cache_key( query, location, days_old )
        if cache_key in _search_cache :
            cached_time, cached_jobs = _search_cache[cache_key]
            if time.time() - cached_time < _cache_ttl :
                logger.info( f"Returning cached jobs for {query} in {location}" )
                return cached_jobs

        logger.info( f"Fetching fresh jobs: query='{query}', location='{location}', max_days={days_old}" )

        # If no API key, return mock data
        if not self.api_key :
            logger.warning( "No SERPAPI_KEY, using mock data" )
            jobs = self._get_mock_jobs( query, location, num_jobs )
            _search_cache[cache_key] = (time.time(), jobs)
            return jobs

        params = {
            "engine" : "google_jobs",
            "q" : f"{query} jobs",
            "location" : location,
            "gl" : "in",
            "hl" : "en",
            "num" : min( num_jobs, 100 ),
            "api_key" : self.api_key,
        }

        try :
            search = GoogleSearch( params )
            results = search.get_dict()
            jobs_results = results.get( "jobs_results", [] )
            logger.info( f"Found {len( jobs_results )} jobs from API" )

            if not jobs_results :
                logger.warning( f"No jobs found from API for '{query}' in {location}, using mock data" )
                jobs = self._get_mock_jobs( query, location, num_jobs )
                _search_cache[cache_key] = (time.time(), jobs)
                return jobs

            jobs = []
            for idx, job in enumerate( jobs_results[:num_jobs] ) :
                title = job.get( "title", "Unknown Title" )
                company = job.get( "company_name", "Unknown Company" )

                posted_at = job.get( "detected_extensions", {} ).get( "posted_at", "" )
                days_old_calc = self._calculate_days_old( posted_at )

                if days_old_calc > days_old :
                    continue

                # Stable content-based ID
                id_source = f"{title}|{company}|{job.get( 'location', '' )}".lower().strip()
                job_id = "job_" + hashlib.md5( id_source.encode() ).hexdigest()[:20]

                job_data = {
                    "id" : job_id,
                    "title" : title,
                    "company" : company,
                    "location" : job.get( "location", location ),
                    "description" : job.get( "description", f"We are hiring for {title} position at {company}" ),
                    "apply_link" : self._extract_apply_link( job ),
                    "posted_at" : posted_at,
                    "employment_type" : job.get( "detected_extensions", {} ).get( "schedule_type", "Full-time" ),
                    "days_old" : days_old_calc,
                    "fetched_at" : datetime.now().isoformat(),
                }
                jobs.append( job_data )

            if not jobs :
                logger.warning( "No jobs after filtering, using mock data" )
                jobs = self._get_mock_jobs( query, location, num_jobs )

            # Cache results
            _search_cache[cache_key] = (time.time(), jobs)

            # Clean old cache entries
            self._clean_cache()

            logger.info( f"Successfully processed {len( jobs )} jobs" )
            return jobs

        except Exception as e :
            logger.error( f"Error fetching jobs: {str( e )}" )
            # Return mock data on error
            jobs = self._get_mock_jobs( query, location, num_jobs )
            _search_cache[cache_key] = (time.time(), jobs)
            return jobs

    def _clean_cache ( self ) :
        """Remove expired cache entries"""
        current_time = time.time()
        expired = [k for k, (t, _) in _search_cache.items() if current_time - t > _cache_ttl]
        for k in expired :
            del _search_cache[k]

    def _calculate_days_old ( self, posted_at: str ) -> int :
        """Calculate how many days old a job posting is"""
        if not posted_at :
            return 0

        posted_lower = posted_at.lower()

        if 'hour' in posted_lower or 'minute' in posted_lower or 'just now' in posted_lower :
            return 0
        elif 'day' in posted_lower :
            match = re.search( r'(\d+)\s*day', posted_lower )
            if match :
                return int( match.group( 1 ) )
            return 1
        elif 'week' in posted_lower :
            match = re.search( r'(\d+)\s*week', posted_lower )
            if match :
                return int( match.group( 1 ) ) * 7
            return 7
        elif 'month' in posted_lower :
            match = re.search( r'(\d+)\s*month', posted_lower )
            if match :
                return int( match.group( 1 ) ) * 30
            return 30
        return 0

    def _extract_apply_link ( self, job: Dict ) -> str :
        """Extract application link from job data"""
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