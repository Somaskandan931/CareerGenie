from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ResumeUploadResponse(BaseModel):
    status: str
    resume_text: str
    word_count: int


class JobMatchRequest(BaseModel):
    resume_text: str
    job_query: str
    location: str = "India"
    num_jobs: int = Field(default=50, ge=1, le=100)
    top_k: int = Field(default=10, ge=1, le=50)
    user_id: Optional[str] = None          # enables adaptive scoring + LTR re-ranking
    min_match_score: float = Field(default=40.0, ge=0, le=100)
    experience_level: Optional[str] = None  # "entry", "mid", "senior"
    posted_within_days: Optional[int] = 14
    exclude_remote: bool = False
    force_refresh: bool = False             # if True, clears vector store before indexing


class JobMatch(BaseModel):
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
    # Per-component scores (stored for LTR feature extraction + feedback attribution)
    semantic_score: Optional[float] = None
    skills_score: Optional[float] = None
    title_score: Optional[float] = None
    # LTR output fields
    ltr_score: Optional[float] = None
    ltr_rank: Optional[int] = None
    personalised: Optional[bool] = False
    # Contribution fractions for EMA weight gradient update
    component_contributions: Optional[Dict[str, float]] = None
    # Uncertainty handler output
    _confidence: Optional[Dict] = None


# Career Advice Models
class SkillGap(BaseModel):
    skill: str
    importance: str
    current_level: str
    target_level: str


class LearningResource(BaseModel):
    title: str
    type: str
    url: Optional[str] = None
    duration: str
    difficulty: str


class CareerStage(BaseModel):
    role: str
    timeline: str
    key_skills_needed: List[str]
    typical_responsibilities: List[str]


class CareerAdviceResponse(BaseModel):
    current_assessment: str
    skill_gaps: List[SkillGap]
    learning_path: List[LearningResource]
    career_progression: List[CareerStage]
    market_insights: str
    action_plan: List[str]
    context_used: Optional[Dict] = None    # which data sources were active


class SkillDetail(BaseModel):
    skill: str
    proficiency: str
    years_experience: int
    context: str


class SkillComparison(BaseModel):
    skill: str
    resume_level: str
    required_level: str
    status: str
    gap_severity: Optional[str] = None


class JobMatchResponse(BaseModel):
    matched_jobs: List[JobMatch]
    total_jobs_fetched: int
    total_jobs_indexed: int
    search_query: str
    career_advice: Optional[CareerAdviceResponse] = None
    skill_comparison: Optional[Dict] = None


class ConfigResponse(BaseModel):
    serpapi_key_present: bool
    searchapi_key_present: bool
    groq_key_present: bool            # primary LLM provider
    anthropic_key_present: bool       # secondary LLM provider
    gemini_key_present: bool          # tertiary LLM provider
    vector_db_initialized: bool
    total_indexed_jobs: int


# ============================================================================
# FEEDBACK ENGINE MODELS
# ============================================================================

class FeedbackRecordRequest(BaseModel):
    user_id: str
    signal_type: str                       # one of REWARD_TABLE keys
    item_id: str                           # job_id / project_id / resource_id
    metadata: Optional[Dict[str, Any]] = None


class FeedbackStatsRequest(BaseModel):
    user_id: str


# ============================================================================
# LEARNING-TO-RANK MODELS
# ============================================================================

class RankingPreferenceRequest(BaseModel):
    """Record that the user preferred winner over loser (pairwise LTR signal)."""
    user_id: str
    winner: Dict[str, Any]                 # job dict (winner of the pair)
    loser: Dict[str, Any]                  # job dict (loser of the pair)
    context: Optional[Dict[str, Any]] = None  # e.g. user_profile


class RankingStatsRequest(BaseModel):
    user_id: str


# ============================================================================
# AGENT ORCHESTRATOR MODELS
# ============================================================================

class AgentRunRequest(BaseModel):
    """Execute a pre-defined multi-agent goal plan."""
    goal: str                              # "full_analysis" | "quick_match" | "interview_prep" | "roadmap_only"
    resume_text: str
    target_role: str = "Software Engineer"
    user_id: Optional[str] = None
    extra_context: Optional[Dict[str, Any]] = None
    stop_on_error: bool = False


class AgentIntentRequest(BaseModel):
    """LLM-planned task decomposition from free-text user intent."""
    intent: str
    resume_text: str
    target_role: str = "Software Engineer"
    user_id: Optional[str] = None


# ============================================================================
# AGENT DEBATE MODELS
# ============================================================================

class DebateRunRequest(BaseModel):
    """Run a full propose → critique → synthesise debate."""
    topic: str
    context: Dict[str, Any]               # cross-agent context dict
    max_rounds: int = Field(default=2, ge=1, le=3)
    resume_text: Optional[str] = None
    user_id: Optional[str] = None


class DebateCritiqueRequest(BaseModel):
    """Quick single-round critique of an existing plan."""
    plan: Dict[str, Any]
    context: Dict[str, Any]


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
    status: Optional[str] = None
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    notes: Optional[str] = None
    progress_pct: Optional[int] = Field(default=None, ge=0, le=100)


class LogDSAProblemRequest(BaseModel):
    user_id: str
    topic: str
    problem_name: str
    difficulty: str = "medium"
    solved: bool = True


class BulkUpdateDSARequest(BaseModel):
    user_id: str
    topic: str
    solved_count: int = Field(ge=0)


class AddInterviewRequest(BaseModel):
    user_id: str
    company: str
    role: str
    source: str = "LinkedIn"


class UpdateInterviewStageRequest(BaseModel):
    user_id: str
    interview_id: str
    new_stage: str
    notes: str = ""


# ============================================================================
# PROGRESS STORE MODELS
# ============================================================================

class DSAProblem(BaseModel):
    problem_id: Optional[str] = None
    topic: str
    title: str
    difficulty: str = "medium"
    leetcode_url: Optional[str] = None
    notes: Optional[str] = None
    solved: bool = False
    attempts: int = 0


class DSAProgressUpdate(BaseModel):
    problem_id: str
    solved: bool
    attempts: Optional[int] = None
    notes: Optional[str] = None


class DSABulkUpdate(BaseModel):
    updates: List[DSAProgressUpdate]


class RoadmapCheckpointUpdate(BaseModel):
    roadmap_id: str
    phase_number: int
    week_number: int
    completed: bool = True
    hours_logged: Optional[float] = 0.0
    notes: Optional[str] = ""


class ProjectStatus(BaseModel):
    project_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    tech_stack: Optional[List[str]] = []
    status: str = "Not Started"
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    progress_percent: int = Field(default=0, ge=0, le=100)
    milestones: Optional[List[str]] = []
    notes: Optional[str] = None


class ProjectStatusUpdate(BaseModel):
    project_id: str
    status: Optional[str] = None
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    progress_percent: Optional[int] = Field(default=None, ge=0, le=100)
    milestone_done: Optional[str] = None
    notes: Optional[str] = None


class InterviewRound(BaseModel):
    round_name: str
    date: Optional[str] = None
    interviewer: Optional[str] = None
    outcome: Optional[str] = None
    notes: Optional[str] = None


class InterviewEntryCreate(BaseModel):
    company: str
    role: str
    job_url: Optional[str] = None
    applied_at: Optional[str] = None


class InterviewRoundAdd(BaseModel):
    interview_id: str
    round: InterviewRound


class InterviewOutcomeUpdate(BaseModel):
    interview_id: str
    final_outcome: str
    offer_details: Optional[Dict] = None
    notes: Optional[str] = None


# ============================================================================
# MENTOR MODELS
# ============================================================================

class MentorSearchRequest(BaseModel):
    expertise: Optional[List[str]] = None
    industry: Optional[str] = None
    language: Optional[str] = None
    max_rate: Optional[float] = None
    min_rating: float = 4.0
    country: Optional[str] = None
    available_now: bool = False


class BookSessionRequest(BaseModel):
    user_id: str
    mentor_id: str
    session_date: str
    session_time: str
    duration_hours: int = 1
    topic: str = ""
    notes: str = ""


class SessionFeedbackRequest(BaseModel):
    user_id: str
    session_id: str
    rating: int = Field(ge=1, le=5)
    feedback: str = ""