from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class ResumeUploadResponse( BaseModel ) :
    status: str
    resume_text: str
    word_count: int


class JobMatchRequest( BaseModel ) :
    resume_text: str
    job_query: str
    location: str = "India"
    num_jobs: int = Field( default=50, ge=1, le=100 )
    top_k: int = Field( default=10, ge=1, le=50 )

    # 🆕 NEW: Filter options
    min_match_score: float = Field( default=40.0, ge=0, le=100 )
    experience_level: Optional[str] = None  # "entry", "mid", "senior"
    posted_within_days: Optional[int] = 14
    exclude_remote: bool = False


class JobMatch( BaseModel ) :
    job_id: str
    title: str
    company: str
    location: str
    match_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    explanation: str
    recommendation: str
    apply_link: Optional[str] = None


# Career Advice Models
class SkillGap( BaseModel ) :
    skill: str
    importance: str
    current_level: str
    target_level: str


class LearningResource( BaseModel ) :
    title: str
    type: str
    url: Optional[str] = None
    duration: str
    difficulty: str


class CareerStage( BaseModel ) :
    role: str
    timeline: str
    key_skills_needed: List[str]
    typical_responsibilities: List[str]


class CareerAdviceResponse( BaseModel ) :
    current_assessment: str
    skill_gaps: List[SkillGap]
    learning_path: List[LearningResource]
    career_progression: List[CareerStage]
    market_insights: str
    action_plan: List[str]


# 🆕 NEW: Skill Analysis Models
class SkillDetail( BaseModel ) :
    skill: str
    proficiency: str
    years_experience: int
    context: str


class SkillComparison( BaseModel ) :
    skill: str
    resume_level: str
    required_level: str
    status: str  # "qualified", "close_match", "gap"
    gap_severity: Optional[str] = None


class JobMatchResponse( BaseModel ) :
    matched_jobs: List[JobMatch]
    total_jobs_fetched: int
    total_jobs_indexed: int
    search_query: str
    career_advice: Optional[CareerAdviceResponse] = None
    skill_comparison: Optional[Dict] = None  # 🆕 NEW: For skill dashboard


class ConfigResponse( BaseModel ) :
    serpapi_key_present: bool
    searchapi_key_present: bool
    anthropic_key_present: bool
    vector_db_initialized: bool
    total_indexed_jobs: int