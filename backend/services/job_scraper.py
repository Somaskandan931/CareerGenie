from typing import List, Dict
from serpapi import GoogleSearch
import logging
from datetime import datetime
import re

from backend.config import settings

logger = logging.getLogger( __name__ )


class JobScraper :
    def __init__ ( self ) :
        if not settings.SERPAPI_KEY :
            raise ValueError( "SERPAPI_KEY not configured" )

        self.api_key = settings.SERPAPI_KEY

    def fetch_jobs ( self, query: str, location: str, num_jobs: int = 50,
                     days_old: int = 7 ) -> List[Dict] :
        """
        Fetch jobs from Google Jobs via SerpAPI with freshness control

        Args:
            query: Job search query (e.g., "software engineer")
            location: Location (e.g., "India", "Bangalore")
            num_jobs: Number of jobs to fetch
            days_old: Maximum age of jobs in days

        Returns:
            List of job dictionaries with freshness metadata
        """
        logger.info( f"Fetching fresh jobs: query='{query}', location='{location}', max_days={days_old}" )

        # Add date filter to query
        date_filter = ""
        if days_old <= 1 :
            date_filter = "&fromage=1"
        elif days_old <= 3 :
            date_filter = "&fromage=3"
        elif days_old <= 7 :
            date_filter = "&fromage=7"
        elif days_old <= 14 :
            date_filter = "&fromage=14"
        elif days_old <= 30 :
            date_filter = "&fromage=30"

        params = {
            "engine" : "google_jobs",
            "q" : f"{query} jobs",
            "location" : location,  # e.g., Bengaluru, Chennai, Remote
            "gl" : "in",  # Country = India (CRITICAL)
            "hl" : "en",  # Language = English
            "num" : min( num_jobs, 100 ),  # API limit
            "api_key" : self.api_key,
            "chips" : f"date_posted:{self._get_date_chip( days_old )}" if days_old < 30 else ""
        }

        try :
            search = GoogleSearch( params )
            results = search.get_dict()

            jobs_results = results.get( "jobs_results", [] )
            logger.info( f"Found {len( jobs_results )} jobs" )

            jobs = []
            for idx, job in enumerate( jobs_results[:num_jobs] ) :
                # Safely extract fields first
                title = job.get( "title", "Unknown Title" )
                company = job.get( "company_name", "Unknown Company" )

                # Calculate days old from posted_at
                posted_at = job.get( "detected_extensions", {} ).get( "posted_at", "" )
                days_old_calc = self._calculate_days_old( posted_at )

                # Skip if older than requested
                if days_old_calc > days_old :
                    continue

                job_data = {
                    "id" : f"job_{idx}_{abs( hash( title + company + datetime.now().isoformat() ) )}",
                    # Unique with timestamp
                    "title" : title,
                    "company" : company,
                    "location" : job.get( "location", location ),
                    "description" : job.get( "description", "" ),
                    "apply_link" : self._extract_apply_link( job ),
                    "posted_at" : posted_at,
                    "employment_type" : job.get( "detected_extensions", {} ).get( "schedule_type", "Full-time" ),
                    "days_old" : days_old_calc,
                    "fetched_at" : datetime.now().isoformat(),
                }

                jobs.append( job_data )

            logger.info( f"Successfully processed {len( jobs )} fresh jobs" )
            return jobs

        except Exception as e :
            logger.error( f"Error fetching jobs: {str( e )}" )
            raise Exception( f"Failed to fetch jobs: {str( e )}" )

    def _get_date_chip ( self, days_old: int ) -> str :
        """Convert days to Google Jobs date chip"""
        if days_old <= 1 :
            return "today"
        elif days_old <= 3 :
            return "3days"
        elif days_old <= 7 :
            return "week"
        elif days_old <= 14 :
            return "2weeks"
        elif days_old <= 30 :
            return "month"
        return ""

    def _calculate_days_old ( self, posted_at: str ) -> int :
        """Calculate how many days old a job posting is"""
        if not posted_at :
            return 0

        posted_lower = posted_at.lower()

        # Parse relative dates
        if 'hour' in posted_lower or 'minute' in posted_lower or 'just now' in posted_lower :
            return 0
        elif 'day' in posted_lower :
            match = re.search( r'(\d+)\s*day', posted_lower )
            if match :
                return int( match.group( 1 ) )
            return 1  # "a day ago" or "yesterday"
        elif 'week' in posted_lower :
            match = re.search( r'(\d+)\s*week', posted_lower )
            if match :
                return int( match.group( 1 ) ) * 7
            return 7  # "a week ago"
        elif 'month' in posted_lower :
            match = re.search( r'(\d+)\s*month', posted_lower )
            if match :
                return int( match.group( 1 ) ) * 30
            return 30  # "a month ago"

        return 0

    def _extract_apply_link ( self, job: Dict ) -> str :
        """Extract application link from job data"""
        # Try related links first
        related_links = job.get( "related_links", [] )
        if related_links and isinstance( related_links, list ) :
            for link in related_links :
                if link.get( "link", "" ) :
                    return link.get( "link", "" )

        # Fallback to share link
        return job.get( "share_link", "" )


# Singleton instance
_job_scraper = None


def get_job_scraper () :
    global _job_scraper
    if _job_scraper is None :
        _job_scraper = JobScraper()
    return _job_scraper