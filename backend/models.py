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


class SkillDetail( BaseModel ) :
    skill: str
    proficiency: str
    years_experience: int
    context: str


class SkillComparison( BaseModel ) :
    skill: str
    resume_level: str
    required_level: str
    status: str
    gap_severity: Optional[str] = None


class JobMatchResponse( BaseModel ) :
    matched_jobs: List[JobMatch]
    total_jobs_fetched: int
    total_jobs_indexed: int
    search_query: str
    career_advice: Optional[CareerAdviceResponse] = None
    skill_comparison: Optional[Dict] = None


class ConfigResponse( BaseModel ) :
    serpapi_key_present: bool
    searchapi_key_present: bool
    anthropic_key_present: bool
    vector_db_initialized: bool
    total_indexed_jobs: int


# ============================================================================
# PROGRESS TRACKER MODELS
# ============================================================================

class ImportRoadmapRequest(BaseModel):
    user_id: str
    roadmap: Dict  # output of /roadmap/generate


class UpdateTaskRequest(BaseModel):
    user_id: str
    week_key: str   # e.g. "Week 1"
    task_id: str
    done: bool


class ImportProjectsRequest(BaseModel):
    user_id: str
    projects: List[Dict]  # output of /projects/suggest


class UpdateProjectRequest(BaseModel):
    user_id: str
    project_id: str
    status: Optional[str] = None            # "Not Started" | "In Progress" | "Testing" | "Deployed" | "Completed"
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    notes: Optional[str] = None
    progress_pct: Optional[int] = Field(default=None, ge=0, le=100)


class LogDSAProblemRequest(BaseModel):
    user_id: str
    topic: str
    problem_name: str
    difficulty: str = "medium"   # "easy" | "medium" | "hard"
    solved: bool = True


class BulkUpdateDSARequest(BaseModel):
    user_id: str
    topic: str
    solved_count: int = Field(ge=0)


class AddInterviewRequest(BaseModel):
    user_id: str
    company: str
    role: str
    source: str = "LinkedIn"    # LinkedIn | Referral | Company Website | etc.


class UpdateInterviewStageRequest(BaseModel):
    user_id: str
    interview_id: str
    new_stage: str   # one of PIPELINE_STAGES
    notes: str = ""


# ============================================================================
# PROGRESS STORE MODELS  (used by main.py progress_store endpoints)
# ============================================================================

class DSAProblem(BaseModel):
    """A single DSA practice problem."""
    problem_id: Optional[str] = None          # auto-generated if omitted
    topic: str                                 # e.g. "Arrays & Hashing"
    title: str                                 # problem name / title
    difficulty: str = "medium"                 # "easy" | "medium" | "hard"
    leetcode_url: Optional[str] = None
    notes: Optional[str] = None
    solved: bool = False
    attempts: int = 0


class DSAProgressUpdate(BaseModel):
    """Mark a single DSA problem solved/unsolved."""
    problem_id: str
    solved: bool
    attempts: Optional[int] = None
    notes: Optional[str] = None


class DSABulkUpdate(BaseModel):
    """Bulk-update multiple DSA problems in one request."""
    updates: List[DSAProgressUpdate]


class RoadmapCheckpointUpdate(BaseModel):
    """Mark a roadmap week/phase checkpoint as complete."""
    roadmap_id: str
    phase_number: int
    week_number: int
    completed: bool = True
    hours_logged: Optional[float] = 0.0
    notes: Optional[str] = ""


class ProjectStatus(BaseModel):
    """Full project entry for the portfolio tracker."""
    project_id: Optional[str] = None          # auto-generated if omitted
    title: str
    description: Optional[str] = None
    tech_stack: Optional[List[str]] = []
    status: str = "Not Started"                # "Not Started" | "In Progress" | "Testing" | "Deployed" | "Completed"
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    progress_percent: int = Field(default=0, ge=0, le=100)
    milestones: Optional[List[str]] = []
    notes: Optional[str] = None


class ProjectStatusUpdate(BaseModel):
    """Partial update for a project entry."""
    project_id: str
    status: Optional[str] = None
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    progress_percent: Optional[int] = Field(default=None, ge=0, le=100)
    milestone_done: Optional[str] = None       # name of a milestone to mark complete
    notes: Optional[str] = None


class InterviewRound(BaseModel):
    """A single round within an interview pipeline entry."""
    round_name: str                            # e.g. "Technical Round 1"
    date: Optional[str] = None                 # ISO date string
    interviewer: Optional[str] = None
    outcome: Optional[str] = None             # "passed" | "failed" | "pending"
    notes: Optional[str] = None


class InterviewEntryCreate(BaseModel):
    """Create a new interview / job application entry."""
    company: str
    role: str
    job_url: Optional[str] = None
    applied_at: Optional[str] = None          # ISO date string; defaults to today


class InterviewRoundAdd(BaseModel):
    """Add a new round to an existing interview entry."""
    interview_id: str
    round: InterviewRound


class InterviewOutcomeUpdate(BaseModel):
    """Set the final outcome of an interview process."""
    interview_id: str
    final_outcome: str                         # "offer" | "rejected" | "withdrawn"
    offer_details: Optional[Dict] = None       # salary, joining date, etc.
    notes: Optional[str] = None