from typing import List, Dict, Optional
from datetime import datetime, timedelta
import re


class SmartJobFilter :
    """Filter jobs based on user preferences and quality signals"""

    def __init__ ( self ) :
        # Red flag keywords (likely scams or low quality)
        self.red_flags = [
            "work from home", "earn money fast", "no experience needed",
            "make $$$ from home", "commission only", "pyramid",
            "multi-level marketing", "mlm"
        ]

        # Quality indicators
        self.quality_indicators = [
            "competitive salary", "benefits", "401k", "health insurance",
            "remote option", "hybrid", "career growth", "training provided"
        ]

        # Experience level patterns
        self.experience_patterns = {
            "entry" : r'\b(entry.?level|junior|0-2\s*years?|fresh|graduate)\b',
            "mid" : r'\b(mid.?level|intermediate|2-5\s*years?|3-5\s*years?)\b',
            "senior" : r'\b(senior|lead|5\+?\s*years?|7\+?\s*years?|expert)\b'
        }

    def filter_jobs (
            self,
            jobs: List[Dict],
            min_match_score: float = 40.0,
            experience_level: Optional[str] = None,
            exclude_remote: bool = False,
            posted_within_days: Optional[int] = None,
            min_quality_score: float = 3.0
    ) -> List[Dict] :
        """Filter jobs based on multiple criteria"""

        filtered = []

        for job in jobs :
            # Skip if below minimum match score
            if job.get( 'match_score', 0 ) < min_match_score :
                continue

            # Calculate quality score
            quality = self._calculate_quality_score( job )
            if quality < min_quality_score :
                continue

            # Filter by experience level
            if experience_level :
                if not self._matches_experience_level( job, experience_level ) :
                    continue

            # Filter by posting date
            if posted_within_days :
                if not self._is_recent( job, posted_within_days ) :
                    continue

            # Filter remote/on-site
            if exclude_remote :
                if self._is_remote( job ) :
                    continue

            # Add quality score to job
            job['quality_score'] = quality
            filtered.append( job )

        # Sort by match score and quality
        filtered.sort(
            key=lambda x : (x.get( 'match_score', 0 ) * 0.7 + x['quality_score'] * 30),
            reverse=True
        )

        return filtered

    def _calculate_quality_score ( self, job: Dict ) -> float :
        """Calculate job quality score (0-10)"""
        score = 5.0  # Base score

        title = job.get( 'title', '' ).lower()
        description = job.get( 'description', '' ).lower()
        company = job.get( 'company', '' ).lower()

        full_text = f"{title} {description} {company}"

        # Penalize red flags
        red_flag_count = sum( 1 for flag in self.red_flags if flag in full_text )
        score -= red_flag_count * 2

        # Reward quality indicators
        quality_count = sum( 1 for indicator in self.quality_indicators if indicator in full_text )
        score += quality_count * 0.5

        # Reward detailed job descriptions
        if len( description ) > 500 :
            score += 1.0
        elif len( description ) < 100 :
            score -= 1.0

        # Check if company name looks legitimate
        if company and len( company ) > 3 and not any( char.isdigit() for char in company ) :
            score += 0.5

        # Has apply link
        if job.get( 'apply_link' ) :
            score += 0.5

        return max( 0, min( 10, score ) )

    def _matches_experience_level ( self, job: Dict, target_level: str ) -> bool :
        """Check if job matches target experience level"""
        title = job.get( 'title', '' ).lower()
        description = job.get( 'description', '' ).lower()
        full_text = f"{title} {description}"

        pattern = self.experience_patterns.get( target_level.lower() )
        if not pattern :
            return True  # Unknown level, don't filter

        return bool( re.search( pattern, full_text, re.IGNORECASE ) )

    def _is_recent ( self, job: Dict, max_days: int ) -> bool :
        """Check if job was posted within max_days"""
        posted_at = job.get( 'posted_at', '' ).lower()

        if not posted_at :
            return True  # Unknown date, include by default

        # Parse relative dates
        if 'day' in posted_at :
            match = re.search( r'(\d+)\s*day', posted_at )
            if match :
                days_ago = int( match.group( 1 ) )
                return days_ago <= max_days

        if 'hour' in posted_at :
            return True  # Posted today

        if 'week' in posted_at :
            match = re.search( r'(\d+)\s*week', posted_at )
            if match :
                weeks_ago = int( match.group( 1 ) )
                return (weeks_ago * 7) <= max_days

        if 'month' in posted_at :
            match = re.search( r'(\d+)\s*month', posted_at )
            if match :
                months_ago = int( match.group( 1 ) )
                return (months_ago * 30) <= max_days

        return True  # Can't parse, include by default

    def _is_remote ( self, job: Dict ) -> bool :
        """Check if job is remote"""
        location = job.get( 'location', '' ).lower()
        description = job.get( 'description', '' ).lower()

        remote_keywords = ['remote', 'work from home', 'wfh', 'anywhere']

        return any( keyword in location or keyword in description for keyword in remote_keywords )

    def get_filter_stats ( self, jobs: List[Dict] ) -> Dict :
        """Get statistics about job filtering"""
        total = len( jobs )

        experience_levels = {'entry' : 0, 'mid' : 0, 'senior' : 0, 'unknown' : 0}
        remote_count = 0
        quality_distribution = {'high' : 0, 'medium' : 0, 'low' : 0}

        for job in jobs :
            # Count experience levels
            title_desc = f"{job.get( 'title', '' )} {job.get( 'description', '' )}".lower()

            level_found = False
            for level, pattern in self.experience_patterns.items() :
                if re.search( pattern, title_desc, re.IGNORECASE ) :
                    experience_levels[level] += 1
                    level_found = True
                    break

            if not level_found :
                experience_levels['unknown'] += 1

            # Count remote
            if self._is_remote( job ) :
                remote_count += 1

            # Quality distribution
            quality = self._calculate_quality_score( job )
            if quality >= 7 :
                quality_distribution['high'] += 1
            elif quality >= 5 :
                quality_distribution['medium'] += 1
            else :
                quality_distribution['low'] += 1

        return {
            'total_jobs' : total,
            'experience_levels' : experience_levels,
            'remote_jobs' : remote_count,
            'quality_distribution' : quality_distribution
        }


# Usage Example
if __name__ == "__main__" :
    # Sample jobs
    jobs = [
        {
            'title' : 'Senior Machine Learning Engineer',
            'company' : 'Tech Corp',
            'description' : 'Looking for senior ML engineer with 5+ years experience. Competitive salary, health insurance, remote option available.',
            'location' : 'San Francisco, CA',
            'match_score' : 85,
            'posted_at' : '2 days ago',
            'apply_link' : 'https://example.com/apply'
        },
        {
            'title' : 'Junior Python Developer',
            'company' : 'Startup Inc',
            'description' : 'Entry-level position for fresh graduates. Training provided.',
            'location' : 'Remote',
            'match_score' : 65,
            'posted_at' : '1 week ago',
            'apply_link' : 'https://example.com/apply'
        },
        {
            'title' : 'Work From Home - Earn $$$',
            'company' : '123',
            'description' : 'Make money fast! No experience needed!',
            'location' : 'Anywhere',
            'match_score' : 70,
            'posted_at' : '3 weeks ago',
            'apply_link' : None
        }
    ]

    filter_engine = SmartJobFilter()

    # Filter for senior roles, high quality, posted in last 14 days
    filtered = filter_engine.filter_jobs(
        jobs,
        min_match_score=60,
        experience_level='senior',
        posted_within_days=14,
        min_quality_score=5.0
    )

    print( "=== FILTERED JOBS ===" )
    for job in filtered :
        print( f"\n{job['title']} at {job['company']}" )
        print( f"  Match: {job['match_score']}% | Quality: {job['quality_score']:.1f}/10" )
        print( f"  Location: {job['location']}" )

    print( "\n\n=== FILTER STATISTICS ===" )
    stats = filter_engine.get_filter_stats( jobs )
    print( f"Total jobs analyzed: {stats['total_jobs']}" )
    print( f"Experience levels: {stats['experience_levels']}" )
    print( f"Remote jobs: {stats['remote_jobs']}" )
    print( f"Quality: {stats['quality_distribution']}" )