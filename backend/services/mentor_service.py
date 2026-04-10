"""
Expert Mentor Service
Connects users with industry experts for paid mentoring calls
"""
from typing import List, Dict, Optional
import logging
import uuid
from datetime import datetime, timedelta
import json
from pathlib import Path

logger = logging.getLogger( __name__ )

# Mentor database with global experts
MENTOR_DATABASE = [
    # Tech / Software Engineering
    {
        "mentor_id" : "mentor_swe_001",
        "name" : "Dr. Sarah Chen",
        "title" : "Principal Engineer",
        "company" : "Google (YouTube)",
        "location" : "USA",
        "country" : "United States",
        "timezone" : "America/Los_Angeles",
        "languages" : ["English", "Mandarin"],
        "expertise" : ["System Design", "Distributed Systems", "Technical Leadership"],
        "industries" : ["Tech", "Software"],
        "experience_years" : 15,
        "hourly_rate" : 150,
        "currency" : "USD",
        "bio" : "Former Amazon and Google engineer. Mentored 50+ engineers into FAANG.",
        "available" : True,
        "rating" : 4.9,
        "total_sessions" : 342,
        "languages_spoken" : ["English", "Mandarin"]
    },
    {
        "mentor_id" : "mentor_swe_002",
        "name" : "Rajesh Kumar",
        "title" : "Engineering Director",
        "company" : "Microsoft India",
        "location" : "India",
        "country" : "India",
        "timezone" : "Asia/Kolkata",
        "languages" : ["English", "Hindi", "Tamil"],
        "expertise" : ["Cloud Architecture", "Azure", "Team Management", "Career Growth"],
        "industries" : ["Tech", "Cloud"],
        "experience_years" : 18,
        "hourly_rate" : 120,
        "currency" : "USD",
        "bio" : "Built multiple Azure services. Passionate about mentoring Indian tech professionals.",
        "available" : True,
        "rating" : 4.8,
        "total_sessions" : 287,
        "languages_spoken" : ["English", "Hindi", "Tamil"]
    },
    {
        "mentor_id" : "mentor_swe_003",
        "name" : "Maria Garcia",
        "title" : "Staff Data Scientist",
        "company" : "Netflix",
        "location" : "Spain",
        "country" : "Spain",
        "timezone" : "Europe/Madrid",
        "languages" : ["English", "Spanish"],
        "expertise" : ["Machine Learning", "Recommendation Systems", "MLOps"],
        "industries" : ["Tech", "Data Science"],
        "experience_years" : 10,
        "hourly_rate" : 180,
        "currency" : "EUR",
        "bio" : "ML expert specializing in personalization. PhD in Computer Science.",
        "available" : True,
        "rating" : 5.0,
        "total_sessions" : 156,
        "languages_spoken" : ["English", "Spanish"]
    },

    # Data Science / AI
    {
        "mentor_id" : "mentor_ds_001",
        "name" : "Dr. Aisha Mohammed",
        "title" : "Head of AI",
        "company" : "DeepMind",
        "location" : "UK",
        "country" : "United Kingdom",
        "timezone" : "Europe/London",
        "languages" : ["English", "Arabic"],
        "expertise" : ["Deep Learning", "Reinforcement Learning", "Research"],
        "industries" : ["AI", "Research"],
        "experience_years" : 12,
        "hourly_rate" : 250,
        "currency" : "GBP",
        "bio" : "DeepMind researcher. Published 20+ papers at NeurIPS, ICML.",
        "available" : True,
        "rating" : 4.9,
        "total_sessions" : 98,
        "languages_spoken" : ["English", "Arabic"]
    },
    {
        "mentor_id" : "mentor_ds_002",
        "name" : "Wei Zhang",
        "title" : "Lead Data Scientist",
        "company" : "Alibaba",
        "location" : "China",
        "country" : "China",
        "timezone" : "Asia/Shanghai",
        "languages" : ["English", "Mandarin"],
        "expertise" : ["Big Data", "Spark", "Recommendation Engines"],
        "industries" : ["Tech", "E-commerce"],
        "experience_years" : 9,
        "hourly_rate" : 100,
        "currency" : "USD",
        "bio" : "Built Alibaba's product recommendation system. Fluent in English.",
        "available" : True,
        "rating" : 4.7,
        "total_sessions" : 203,
        "languages_spoken" : ["English", "Mandarin"]
    },

    # Automotive / EV
    {
        "mentor_id" : "mentor_auto_001",
        "name" : "Klaus Mueller",
        "title" : "VP of Engineering",
        "company" : "BMW",
        "location" : "Germany",
        "country" : "Germany",
        "timezone" : "Europe/Berlin",
        "languages" : ["English", "German"],
        "expertise" : ["EV Engineering", "Battery Systems", "Automotive Manufacturing"],
        "industries" : ["Automotive", "EV"],
        "experience_years" : 22,
        "hourly_rate" : 300,
        "currency" : "EUR",
        "bio" : "20+ years in German automotive industry. Expert in EV platforms.",
        "available" : True,
        "rating" : 5.0,
        "total_sessions" : 67,
        "languages_spoken" : ["English", "German"]
    },
    {
        "mentor_id" : "mentor_auto_002",
        "name" : "Priya Sundar",
        "title" : "Senior Engineer",
        "company" : "Tesla",
        "location" : "USA",
        "country" : "United States",
        "timezone" : "America/Chicago",
        "languages" : ["English", "Tamil"],
        "expertise" : ["Battery Management Systems", "Power Electronics", "EV Testing"],
        "industries" : ["Automotive", "EV"],
        "experience_years" : 8,
        "hourly_rate" : 140,
        "currency" : "USD",
        "bio" : "Tesla battery engineer. Helped design Model Y battery pack.",
        "available" : True,
        "rating" : 4.8,
        "total_sessions" : 124,
        "languages_spoken" : ["English", "Tamil"]
    },

    # Product Management
    {
        "mentor_id" : "mentor_pm_001",
        "name" : "James Wilson",
        "title" : "Director of Product",
        "company" : "Meta",
        "location" : "USA",
        "country" : "United States",
        "timezone" : "America/New_York",
        "languages" : ["English"],
        "expertise" : ["Product Strategy", "User Research", "Go-to-Market"],
        "industries" : ["Tech", "Product"],
        "experience_years" : 14,
        "hourly_rate" : 200,
        "currency" : "USD",
        "bio" : "Led products at Facebook and Instagram. Expert in product-led growth.",
        "available" : True,
        "rating" : 4.9,
        "total_sessions" : 189,
        "languages_spoken" : ["English"]
    },
    {
        "mentor_id" : "mentor_pm_002",
        "name" : "Yuki Tanaka",
        "title" : "Principal Product Manager",
        "company" : "Sony",
        "location" : "Japan",
        "country" : "Japan",
        "timezone" : "Asia/Tokyo",
        "languages" : ["English", "Japanese"],
        "expertise" : ["Consumer Electronics", "Hardware Product", "Japanese Market"],
        "industries" : ["Consumer Electronics", "Hardware"],
        "experience_years" : 16,
        "hourly_rate" : 150,
        "currency" : "USD",
        "bio" : "Launched PlayStation products. Expert in Japanese consumer market.",
        "available" : True,
        "rating" : 4.8,
        "total_sessions" : 92,
        "languages_spoken" : ["English", "Japanese"]
    },

    # Career Coaching
    {
        "mentor_id" : "mentor_career_001",
        "name" : "Carlos Mendez",
        "title" : "Executive Coach",
        "company" : "Independent",
        "location" : "Mexico",
        "country" : "Mexico",
        "timezone" : "America/Mexico_City",
        "languages" : ["English", "Spanish"],
        "expertise" : ["Career Transition", "Leadership", "Interview Prep"],
        "industries" : ["All"],
        "experience_years" : 12,
        "hourly_rate" : 100,
        "currency" : "USD",
        "bio" : "Helped 200+ professionals transition into tech from non-tech backgrounds.",
        "available" : True,
        "rating" : 4.9,
        "total_sessions" : 412,
        "languages_spoken" : ["English", "Spanish"]
    },
]

# Session storage
MENTOR_SESSIONS_FILE = Path( "/tmp/career_genie_mentor_sessions.json" )


class MentorService :
    def __init__ ( self ) :
        self.mentors = MENTOR_DATABASE
        self._load_sessions()

    def _load_sessions ( self ) :
        """Load existing sessions from file"""
        if MENTOR_SESSIONS_FILE.exists() :
            try :
                with open( MENTOR_SESSIONS_FILE, 'r' ) as f :
                    self.sessions = json.load( f )
            except :
                self.sessions = []
        else :
            self.sessions = []

    def _save_sessions ( self ) :
        """Save sessions to file"""
        with open( MENTOR_SESSIONS_FILE, 'w' ) as f :
            json.dump( self.sessions, f, indent=2 )

    def search_mentors ( self,
                         expertise: Optional[List[str]] = None,
                         industry: Optional[str] = None,
                         language: Optional[str] = None,
                         max_rate: Optional[float] = None,
                         min_rating: float = 4.0,
                         country: Optional[str] = None,
                         available_now: bool = False ) -> List[Dict] :
        """
        Search for mentors based on filters
        """
        results = self.mentors.copy()

        if expertise :
            expertise_lower = [e.lower() for e in expertise]
            results = [
                m for m in results
                if any( e in [exp.lower() for exp in m['expertise']] for e in expertise_lower )
            ]

        if industry :
            results = [
                m for m in results
                if industry.lower() in [ind.lower() for ind in m['industries']] or "All" in m['industries']
            ]

        if language :
            results = [
                m for m in results
                if language.lower() in [lang.lower() for lang in m['languages_spoken']]
            ]

        if max_rate :
            results = [m for m in results if m['hourly_rate'] <= max_rate]

        if min_rating :
            results = [m for m in results if m['rating'] >= min_rating]

        if country :
            results = [m for m in results if m['country'].lower() == country.lower()]

        if available_now :
            # Simple availability check - in production, check calendar
            results = [m for m in results if m['available']]

        return results

    def get_mentor_by_id ( self, mentor_id: str ) -> Optional[Dict] :
        """Get mentor details by ID"""
        for mentor in self.mentors :
            if mentor['mentor_id'] == mentor_id :
                return mentor
        return None

    def book_session ( self, user_id: str, mentor_id: str, session_date: str,
                       session_time: str, duration_hours: int = 1, topic: str = "",
                       notes: str = "" ) -> Dict :
        """
        Book a mentoring session
        """
        mentor = self.get_mentor_by_id( mentor_id )
        if not mentor :
            return {"error" : "Mentor not found"}

        session_id = str( uuid.uuid4() )

        session = {
            "session_id" : session_id,
            "user_id" : user_id,
            "mentor_id" : mentor_id,
            "mentor_name" : mentor['name'],
            "mentor_title" : mentor['title'],
            "mentor_company" : mentor['company'],
            "session_date" : session_date,
            "session_time" : session_time,
            "duration_hours" : duration_hours,
            "total_cost" : mentor['hourly_rate'] * duration_hours,
            "currency" : mentor['currency'],
            "topic" : topic,
            "notes" : notes,
            "status" : "pending",
            "created_at" : datetime.utcnow().isoformat(),  # Store as string, not datetime object
            "payment_status" : "pending"
        }

        self.sessions.append( session )
        self._save_sessions()
        return session

    def get_user_sessions ( self, user_id: str ) -> List[Dict] :
        """Get all sessions for a user"""
        sessions = [s for s in self.sessions if s['user_id'] == user_id]
        # Ensure all datetime fields are strings
        for s in sessions :
            if "created_at" in s and hasattr( s["created_at"], "isoformat" ) :
                s["created_at"] = s["created_at"].isoformat()
            if "completed_at" in s and hasattr( s["completed_at"], "isoformat" ) :
                s["completed_at"] = s["completed_at"].isoformat()
            if "cancelled_at" in s and hasattr( s["cancelled_at"], "isoformat" ) :
                s["cancelled_at"] = s["cancelled_at"].isoformat()
        return sessions

    def cancel_session ( self, session_id: str, user_id: str ) -> Dict :
        """Cancel a session"""
        for session in self.sessions :
            if session['session_id'] == session_id and session['user_id'] == user_id :
                if session['status'] == 'pending' or session['status'] == 'confirmed' :
                    session['status'] = 'cancelled'
                    session['cancelled_at'] = datetime.utcnow().isoformat()
                    self._save_sessions()
                    return {"success" : True, "session" : session}
                return {"error" : "Cannot cancel session in current status"}
        return {"error" : "Session not found"}

    def complete_session ( self, session_id: str, user_id: str, rating: Optional[int] = None,
                           feedback: str = "" ) -> Dict :
        """Mark a session as completed and leave feedback"""
        for session in self.sessions :
            if session['session_id'] == session_id and session['user_id'] == user_id :
                if session['status'] == 'confirmed' :
                    session['status'] = 'completed'
                    session['completed_at'] = datetime.utcnow().isoformat()
                    if rating :
                        session['user_rating'] = rating
                    if feedback :
                        session['user_feedback'] = feedback
                    self._save_sessions()
                    return {"success" : True, "session" : session}
                return {"error" : "Session not confirmed"}
        return {"error" : "Session not found"}

    def get_available_slots ( self, mentor_id: str, date: str ) -> List[str] :
        """
        Get available time slots for a mentor on a specific date
        Simplified implementation - in production, integrate with calendar API
        """
        # Mock available slots
        slots = [
            "09:00", "10:00", "11:00", "14:00", "15:00", "16:00"
        ]

        # Remove booked slots
        booked_slots = []
        for session in self.sessions :
            if (session['mentor_id'] == mentor_id and
                    session['session_date'] == date and
                    session['status'] in ['pending', 'confirmed']) :
                booked_slots.append( session['session_time'] )

        return [slot for slot in slots if slot not in booked_slots]

    def get_mentor_reviews ( self, mentor_id: str ) -> List[Dict] :
        """Get all reviews for a mentor"""
        reviews = []
        for session in self.sessions :
            if (session['mentor_id'] == mentor_id and
                    session['status'] == 'completed' and
                    'user_rating' in session) :
                reviews.append( {
                    "user_id" : session['user_id'],
                    "rating" : session['user_rating'],
                    "feedback" : session.get( 'user_feedback', '' ),
                    "date" : session['completed_at'],
                    "topic" : session['topic']
                } )
        return reviews


# Singleton
_mentor_service = None


def get_mentor_service () :
    global _mentor_service
    if _mentor_service is None :
        _mentor_service = MentorService()
    return _mentor_service