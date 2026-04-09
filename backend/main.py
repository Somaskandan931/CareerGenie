from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Tuple
import tempfile
import os
import logging
from pathlib import Path
from datetime import datetime

from backend.config import settings

# Add these imports at the top if not already present
import hashlib
import threading
import asyncio
from functools import wraps
from collections import defaultdict

# ── Request deduplication for job matching ────────────────────────────────────
_pending_job_matches: Dict[str, asyncio.Future] = {}
_pending_lock = threading.Lock()


def deduplicate_job_matches ( func ) :
    """Decorator to prevent duplicate concurrent job match requests."""

    @wraps( func )
    async def wrapper ( request, *args, **kwargs ) :
        # Create a unique key for this request
        key_data = f"{request.resume_text[:500]}|{request.job_query}|{request.location}|{request.user_id}"
        key = hashlib.md5( key_data.encode() ).hexdigest()

        with _pending_lock :
            if key in _pending_job_matches :
                logger.info( f"Deduplicating job match request: {key[:8]}" )
                return await _pending_job_matches[key]

            # Create a future for this request
            future = asyncio.Future()
            _pending_job_matches[key] = future

        try :
            result = await func( request, *args, **kwargs )
            future.set_result( result )
            return result
        except Exception as e :
            future.set_exception( e )
            raise
        finally :
            with _pending_lock :
                _pending_job_matches.pop( key, None )

    return wrapper

# ── Gemini client (google-genai SDK) ─────────────────────────────────────────
try:
    from google import genai
    _genai_client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None
except Exception as _genai_err:
    _genai_client = None
    genai = None
    logging.warning(f"google-genai not available: {_genai_err}. Run: pip install google-genai")
from backend.models import (
    ResumeUploadResponse, JobMatchRequest, JobMatchResponse,
    ConfigResponse, JobMatch,
    # Feedback & LTR
    FeedbackRecordRequest, RankingPreferenceRequest,
    # Agent orchestrator
    AgentRunRequest, AgentIntentRequest,
    # Debate
    DebateRunRequest, DebateCritiqueRequest,
)
from backend.services.resume_parser import resume_parser
from backend.services.vector_store import vector_store
from backend.services.matcher import get_job_matcher
from backend.services.career_advisor import career_advisor
from backend.services.job_scraper import get_job_scraper
from backend.services.roadmap_generator import get_roadmap_generator
from backend.services.project_generator import get_project_generator
from backend.services.tn_automotive_taxonomy import tn_extractor, NSQF_LEVELS, TN_SKILL_DB
from backend.services.job_coach import get_job_coach
from backend.services.market_insights import get_market_insights
from backend.services.interview_coach import get_interview_coach
from backend.services.progress_store import progress_store
from backend.services.progress_tracker import get_progress_tracker
from backend.services.ats_scorer import ats_scorer
from backend.services.resume_rewriter import resume_rewriter
from backend.models import (
    DSAProblem, DSAProgressUpdate, DSABulkUpdate,
    RoadmapCheckpointUpdate,
    ProjectStatus, ProjectStatusUpdate,
    InterviewEntryCreate, InterviewRoundAdd, InterviewOutcomeUpdate,
    InterviewRound,
)
from backend.services.mentor_service import get_mentor_service
from backend.models import MentorSearchRequest, BookSessionRequest, SessionFeedbackRequest

# New services
from backend.services.feedback_engine import get_feedback_engine
from backend.services.learning_to_rank import get_ltr_engine
from backend.services.agent_orchestrator import get_orchestrator
from backend.services.agent_debate import get_debate_orchestrator
from backend.services.uncertainty_handler import get_uncertainty_handler

logging.basicConfig( level=logging.INFO,
                     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' )
logger = logging.getLogger( __name__ )

# ── Silence the broken ChromaDB/PostHog telemetry (capture() signature mismatch)
try :
    import chromadb.telemetry.product.posthog as _chroma_ph

    _chroma_ph.Posthog = type( "_NoOp", (), {
        "capture" : staticmethod( lambda *a, **kw : None ),
        "shutdown" : staticmethod( lambda *a, **kw : None ),
    } )()
except Exception :
    pass

import hashlib

# ── In-memory career advice cache — avoids hitting API on every request for
#    the same resume+query pair
_advice_cache: dict = {}


# ============================================================================
# LIFESPAN  — must be defined BEFORE app = FastAPI(lifespan=lifespan)
# ============================================================================

@asynccontextmanager
async def lifespan ( app: FastAPI ) :
    # ── Startup ──────────────────────────────────────────────────────────────
    logger.info( "=" * 60 )
    logger.info( "Career Genie – TN AUTO SkillBridge v4.1" )
    logger.info( "=" * 60 )

    settings.ensure_store_dirs()
    Path( settings.CHROMA_PERSIST_DIR ).mkdir( parents=True, exist_ok=True )

    for err in settings.validate() :
        logger.error( f"  ❌ {err}" )
    if not settings.validate() :
        logger.info( "✅ All configurations valid" )

    if _genai_client is None :
        logger.error( "❌ Gemini client NOT initialized — check GEMINI_API_KEY and 'pip install google-genai'" )
    else :
        logger.info( "✅ Gemini client initialized" )

    logger.info( f"✅ TN taxonomy: {len( tn_extractor.skill_db )} skills · {len( tn_extractor.job_roles )} roles" )

    stats = vector_store.get_stats()
    logger.info(
        f"✅ Vector store: {stats['total_jobs']} jobs indexed · freshness: {stats.get( 'freshness', 'unknown' )}" )

    logger.info( "✅ Engines ready: Feedback · LTR · Agent Orchestrator · Agent Debate · Uncertainty Handler" )
    logger.info( "=" * 60 )

    yield  # ← app runs here

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info( "Career Genie shutting down." )


app = FastAPI(
    title="Career Genie – TN AUTO SkillBridge",
    description=(
        "AI-powered workforce analytics · Job Coach · Market Insights · "
        "Interview Coach · Resume Rewriter · Agent Debate · Learning-to-Rank"
    ),
    version="4.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)


# ============================================================================
# REQUEST MODELS
# ============================================================================

class RoadmapRequest( BaseModel ) :
    resume_text: str
    target_role: str
    skill_gaps: List[str] = []
    duration_weeks: int = 12
    experience_level: Optional[str] = None


class ProjectRequest( BaseModel ) :
    resume_text: str
    target_role: str
    skill_gaps: List[str] = []
    difficulty: Optional[str] = "intermediate"
    num_projects: int = 5


class TNSkillAnalysisRequest( BaseModel ) :
    profile_text: str
    target_role: Optional[str] = None


class BatchProfileItem( BaseModel ) :
    id: str
    name: str
    text: str
    target_role: Optional[str] = None


class BatchAnalysisRequest( BaseModel ) :
    institution_name: Optional[str] = "Tamil Nadu ITI / Polytechnic"
    profiles: List[BatchProfileItem]


class ChatMessage( BaseModel ) :
    role: str
    content: str


class JobCoachRequest( BaseModel ) :
    messages: List[ChatMessage]
    resume_text: Optional[str] = None


class MarketInsightsRequest( BaseModel ) :
    role: str
    skills: Optional[List[str]] = None
    location: str = "India"


class InterviewChatRequest( BaseModel ) :
    messages: List[ChatMessage]
    role: str
    interview_type: str = "mixed"
    resume_text: Optional[str] = None


class InterviewQuestionsRequest( BaseModel ) :
    role: str
    interview_type: str = "mixed"
    resume_text: Optional[str] = None
    num_questions: int = 10


class EvaluateAnswerRequest( BaseModel ) :
    question: str
    answer: str
    role: str
    interview_type: str = "mixed"


class ResumeRewriteRequest( BaseModel ) :
    resume_text: str
    target_role: str = "Software Engineer"
    tone: str = "professional"


class RoadmapImportRequest( BaseModel ) :
    user_id: str
    roadmap: Dict[str, Any]


class TaskUpdateRequest( BaseModel ) :
    user_id: str
    week_key: str
    task_id: str
    done: bool


class ProjectAddRequest( BaseModel ) :
    user_id: str
    project: Dict[str, Any]


class ProjectUpdateRequest( BaseModel ) :
    user_id: str
    project_id: str
    updates: Dict[str, Any]


class DSALogRequest( BaseModel ) :
    user_id: str
    topic: str
    problem_name: str
    difficulty: str = "medium"
    solved: bool = True


class DSABulkUpdateRequest( BaseModel ) :
    user_id: str
    topic: str
    solved_count: int


class InterviewAddRequest( BaseModel ) :
    user_id: str
    company: str
    role: str
    source: str = "LinkedIn"


class InterviewStageUpdateRequest( BaseModel ) :
    user_id: str
    interview_id: str
    new_stage: str
    notes: str = ""


class ATSScoreRequest( BaseModel ) :
    resume_text: str
    target_role: Optional[str] = None
    job_description: Optional[str] = None  # if provided, score against actual JD


class HRRecruiterRequest( BaseModel ) :
    resume_text: str
    target_role: str
    company_type: str = "startup"  # "startup" | "mid-size" | "enterprise" | "faang"
    focus_area: str = "general"  # "general" | "technical" | "behavioural" | "compensation"
    job_description: Optional[str] = None  # if provided, recruiter evaluates against actual JD


class ResumeAnalyzeRequest( BaseModel ) :
    """Combined request — runs ATS scorer + HR recruiter panel in parallel."""
    resume_text: str
    target_role: str
    job_description: Optional[str] = None
    company_type: str = "startup"
    focus_area: str = "general"


# ============================================================================
# CONFIG
# ============================================================================

@app.get( "/config", response_model=ConfigResponse )
def get_config () :
    return ConfigResponse(
        serpapi_key_present=bool( settings.SERPAPI_KEY ),
        searchapi_key_present=bool( settings.SERPAPI_KEY ),
        groq_key_present=bool( settings.GROQ_API_KEY ),
        anthropic_key_present=bool( settings.ANTHROPIC_API_KEY ),
        gemini_key_present=bool( settings.GEMINI_API_KEY ),
        vector_db_initialized=True,
        total_indexed_jobs=vector_store.collection.count()
    )


# ============================================================================
# RESUME UPLOAD
# ============================================================================

@app.post( "/upload-resume/parse", response_model=ResumeUploadResponse )
async def parse_resume ( file: UploadFile = File( ... ) ) :
    logger.info( f"Resume upload: {file.filename}" )
    if not file.filename.lower().endswith( ('.pdf', '.docx', '.doc') ) :
        raise HTTPException( status_code=400, detail="Invalid format. Upload PDF or DOCX." )
    suffix = Path( file.filename ).suffix
    with tempfile.NamedTemporaryFile( delete=False, suffix=suffix ) as tmp :
        tmp.write( await file.read() )
        temp_path = tmp.name
    try :
        result = resume_parser.parse( temp_path )

        # Confidence check on parsed text
        try :
            uh = get_uncertainty_handler()
            _, parse_report = uh.wrap_parse( result['resume_text'], result['word_count'] )
            if parse_report.should_retry :
                logger.warning( f"Parse confidence low: {parse_report.issues}" )
        except Exception :
            pass

        return ResumeUploadResponse(
            status="success",
            resume_text=result['resume_text'],
            word_count=result['word_count']
        )
    except Exception as e :
        raise HTTPException( status_code=500, detail=f"Failed to parse resume: {e}" )
    finally :
        if os.path.exists( temp_path ) :
            os.remove( temp_path )


# ============================================================================
# JOB MATCHING  — now accepts user_id for adaptive scoring + LTR re-ranking
# ============================================================================

@app.post( "/rag/match-realtime", response_model=JobMatchResponse )
@deduplicate_job_matches
async def match_jobs_realtime ( request: JobMatchRequest ) :
    if not request.resume_text.strip() :
        raise HTTPException( status_code=400, detail="Resume text is required" )
    if not request.job_query.strip() :
        raise HTTPException( status_code=400, detail="Job query is required" )

    force_refresh = request.force_refresh

    try :
        loop = asyncio.get_event_loop()

        # Fetch jobs
        jobs = await loop.run_in_executor(
            None,
            lambda : get_job_scraper().fetch_jobs(
                query=request.job_query,
                location=request.location,
                num_jobs=request.num_jobs,
                days_old=7
            )
        )

        if not jobs :
            return JobMatchResponse(
                matched_jobs=[], total_jobs_fetched=0, total_jobs_indexed=0,
                search_query=f"{request.job_query} in {request.location}"
            )

        # Filter jobs
        try :
            from backend.services.job_filter import SmartJobFilter
            filtered = SmartJobFilter().filter_jobs(
                jobs,
                min_match_score=request.min_match_score,
                experience_level=request.experience_level,
                posted_within_days=request.posted_within_days or 7,
                exclude_remote=request.exclude_remote
            )
            jobs_to_index = filtered if filtered else jobs
        except ImportError :
            jobs_to_index = jobs

        if force_refresh :
            await loop.run_in_executor( None, vector_store.clear )

        indexed_count = await loop.run_in_executor(
            None, lambda : vector_store.index_jobs( jobs_to_index )
        )

        if indexed_count == 0 :
            raise HTTPException( status_code=500, detail="Failed to index jobs" )

        matches = await loop.run_in_executor(
            None,
            lambda : get_job_matcher().match_resume_to_jobs(
                resume_text=request.resume_text,
                top_k=request.top_k,
                force_refresh=False,
                location=request.location,
                user_id=request.user_id,
            )
        )

        # Deduplicate matches by job_id
        seen_ids = set()
        unique_matches = []
        for match in matches :
            job_id = match.get( "job_id" )
            if job_id and job_id not in seen_ids :
                seen_ids.add( job_id )
                unique_matches.append( match )

        matches = unique_matches

        # Career advice — served from cache when possible
        career_advice_data = None
        if career_advisor :
            try :
                resume_hash = hashlib.md5( request.resume_text.encode() ).hexdigest()[:12]
                advice_cache_key = (resume_hash, request.job_query.lower().strip())

                if advice_cache_key in _advice_cache :
                    logger.info( "Career advice served from cache" )
                    career_advice_data = _advice_cache[advice_cache_key]
                else :
                    user_profile = None
                    if request.user_id :
                        try :
                            user_profile = get_feedback_engine().get_profile( request.user_id )
                        except Exception :
                            pass

                    career_advice_data = career_advisor.generate_career_advice(
                        resume_text=request.resume_text,
                        target_role=request.job_query,
                        current_role=None,
                        job_matches=matches[:3],
                        user_profile=user_profile,
                    )
                    _advice_cache[advice_cache_key] = career_advice_data
                    logger.info( "Career advice generated and cached" )

                # Uncertainty check on advice
                try :
                    uh = get_uncertainty_handler()
                    career_advice_data, advice_report = uh.wrap_advice( career_advice_data )
                    career_advice_data['_confidence'] = advice_report.to_dict()
                except Exception :
                    pass

            except Exception as e :
                logger.error( f"Career advice failed: {e}" )

        skill_comparison_data = None
        try :
            if matches :
                matcher = get_job_matcher()
                rs = matcher._extract_skills( request.resume_text )
                js = matcher._extract_skills( matches[0].get( 'description', '' ) )
                skill_comparison_data = {
                    "overall_match" : matches[0].get( 'match_score', 0 ),
                    "matched_skills" : [{"skill" : s, "status" : "qualified"} for s in set( rs ) & set( js )],
                    "skill_gaps" : [{"skill" : s, "resume_level" : "none", "required_level" : "intermediate",
                                     "gap_severity" : "moderate"} for s in set( js ) - set( rs )],
                    "bonus_skills" : [{"skill" : s} for s in set( rs ) - set( js )],
                    "resume_skills" : [{"skill" : s, "category" : "Programming"} for s in rs],
                    "job_skills" : [{"skill" : s, "category" : "Programming"} for s in js],
                }
        except Exception as e :
            logger.error( f"Skill comparison failed: {e}" )

        resp = {
            "matched_jobs" : [JobMatch( **m ) for m in matches],
            "total_jobs_fetched" : len( jobs ),
            "total_jobs_indexed" : indexed_count,
            "search_query" : f"{request.job_query} in {request.location}",
            "freshness" : "fresh" if force_refresh else "cached",
        }

        if career_advice_data :
            resp["career_advice"] = career_advice_data
        if skill_comparison_data :
            resp["skill_comparison"] = skill_comparison_data

        return JobMatchResponse( **resp )

    except HTTPException :
        raise
    except Exception as e :
        logger.error( f"Job matching error: {e}", exc_info=True )
        raise HTTPException( status_code=500, detail=f"Job matching failed: {e}" )
# ============================================================================
# FEEDBACK ENGINE  (/feedback/record and /feedback/stats)
# ============================================================================

@app.post( "/feedback/record" )
def record_feedback ( request: FeedbackRecordRequest ) :
    try :
        updated_weights = get_feedback_engine().record(
            user_id=request.user_id,
            signal_type=request.signal_type,
            item_id=request.item_id,
            metadata=request.metadata or {},
        )
        return {
            "status" : "success",
            "signal_type" : request.signal_type,
            "updated_weights" : updated_weights,
        }
    except Exception as e :
        logger.error( f"Feedback record error: {e}" )
        raise HTTPException( status_code=500, detail=str( e ) )


@app.get( "/feedback/stats" )
def feedback_stats ( user_id: str ) :
    try :
        stats = get_feedback_engine().get_stats( user_id )
        return {"status" : "success", "stats" : stats}
    except Exception as e :
        logger.error( f"Feedback stats error: {e}" )
        raise HTTPException( status_code=500, detail=str( e ) )


# ============================================================================
# LEARNING-TO-RANK  (/ranking/preference and /ranking/stats)
# ============================================================================

@app.post( "/ranking/preference" )
def record_ranking_preference ( request: RankingPreferenceRequest ) :
    try :
        get_ltr_engine().record_preference(
            user_id=request.user_id,
            winner=request.winner,
            loser=request.loser,
            context=request.context or {},
        )
        return {"status" : "success", "message" : "Preference recorded"}
    except Exception as e :
        logger.error( f"LTR preference record error: {e}" )
        raise HTTPException( status_code=500, detail=str( e ) )


@app.get( "/ranking/stats" )
def ranking_stats ( user_id: str ) :
    try :
        stats = get_ltr_engine().get_stats( user_id )
        return {"status" : "success", "stats" : stats}
    except Exception as e :
        logger.error( f"LTR stats error: {e}" )
        raise HTTPException( status_code=500, detail=str( e ) )


# ============================================================================
# AGENT ORCHESTRATOR  (/agent/run and /agent/intent)
# ============================================================================

@app.post( "/agent/run" )
def agent_run ( request: AgentRunRequest ) :
    try :
        orch = get_orchestrator()
        orch.load_resume( request.resume_text, request.target_role )

        result = orch.run_goal(
            goal=request.goal,
            user_id=request.user_id or "",
            extra_context=request.extra_context,
            stop_on_error=request.stop_on_error,
        )
        return {"status" : "success", **result}
    except Exception as e :
        logger.error( f"Agent run error: {e}", exc_info=True )
        raise HTTPException( status_code=500, detail=str( e ) )


@app.post( "/agent/intent" )
def agent_intent ( request: AgentIntentRequest ) :
    try :
        orch = get_orchestrator()
        orch.load_resume( request.resume_text, request.target_role )

        result = orch.plan_from_intent(
            user_intent=request.intent,
            user_id=request.user_id or "",
        )
        return {"status" : "success", **result}
    except Exception as e :
        logger.error( f"Agent intent error: {e}", exc_info=True )
        raise HTTPException( status_code=500, detail=str( e ) )


# ============================================================================
# AGENT DEBATE  (/debate/run and /debate/critique)
# ============================================================================

@app.post( "/debate/run" )
def debate_run ( request: DebateRunRequest ) :
    try :
        debate_orch = get_debate_orchestrator()

        context = dict( request.context )
        if request.resume_text :
            context["resume_text"] = request.resume_text[:1500]
        if request.user_id :
            try :
                context["user_profile"] = get_feedback_engine().get_profile( request.user_id )
            except Exception :
                pass

        result = debate_orch.run_debate(
            topic=request.topic,
            context=context,
            max_rounds=request.max_rounds,
        )
        return {"status" : "success", **debate_orch.to_dict( result )}
    except Exception as e :
        logger.error( f"Debate run error: {e}", exc_info=True )
        raise HTTPException( status_code=500, detail=str( e ) )


@app.post( "/debate/critique" )
def debate_critique ( request: DebateCritiqueRequest ) :
    try :
        result = get_debate_orchestrator().quick_critique(
            plan=request.plan,
            context=request.context,
        )
        return {"status" : "success", "critique" : result}
    except Exception as e :
        logger.error( f"Debate critique error: {e}", exc_info=True )
        raise HTTPException( status_code=500, detail=str( e ) )


# ============================================================================
# ROADMAP & PROJECTS
# ============================================================================

@app.post( "/generate/roadmap" )
def generate_roadmap ( request: RoadmapRequest ) :
    if not request.target_role.strip() :
        raise HTTPException( status_code=400, detail="target_role is required" )
    try :
        roadmap = get_roadmap_generator().generate_roadmap(
            resume_text=request.resume_text, target_role=request.target_role,
            skill_gaps=request.skill_gaps, duration_weeks=request.duration_weeks,
            experience_level=request.experience_level
        )
        return {"status" : "success", "roadmap" : roadmap}
    except Exception as e :
        raise HTTPException( status_code=500, detail=str( e ) )


@app.post( "/generate/projects" )
def generate_projects ( request: ProjectRequest ) :
    if not request.target_role.strip() :
        raise HTTPException( status_code=400, detail="target_role is required" )
    try :
        projects = get_project_generator().suggest_projects(
            resume_text=request.resume_text, target_role=request.target_role,
            skill_gaps=request.skill_gaps, difficulty=request.difficulty,
            num_projects=request.num_projects
        )
        return {"status" : "success", "projects" : projects}
    except Exception as e :
        raise HTTPException( status_code=500, detail=str( e ) )


# Route aliases
@app.post( "/roadmap/generate" )
def generate_roadmap_alias ( request: RoadmapRequest ) :
    return generate_roadmap( request )


@app.post( "/projects/suggest" )
def suggest_projects_alias ( request: ProjectRequest ) :
    return generate_projects( request )


# ============================================================================
# ROADMAP IMPORT
# ============================================================================

@app.post( "/progress/roadmap/import" )
def import_roadmap ( request: RoadmapImportRequest ) :
    try :
        tracker = get_progress_tracker()
        result = tracker.import_roadmap( request.user_id, request.roadmap )
        if "error" in result :
            raise HTTPException( status_code=400, detail=result["error"] )
        roadmap_with_progress = tracker.get_roadmap_with_progress( request.user_id )
        return {"status" : "success", "import_result" : result, "roadmap" : roadmap_with_progress}
    except HTTPException :
        raise
    except Exception as e :
        logger.error( f"Roadmap import error: {e}" )
        raise HTTPException( status_code=500, detail=str( e ) )


@app.get( "/progress/{user_id}/roadmap" )
def get_roadmap_progress ( user_id: str ) :
    try :
        tracker = get_progress_tracker()
        roadmap = tracker.get_roadmap_with_progress( user_id )
        return {"status" : "success", "roadmap" : roadmap}
    except Exception as e :
        raise HTTPException( status_code=500, detail=str( e ) )


@app.post( "/progress/roadmap/task/update" )
def update_roadmap_task ( request: TaskUpdateRequest ) :
    try :
        tracker = get_progress_tracker()
        result = tracker.update_task( request.user_id, request.week_key, request.task_id, request.done )
        if not result.get( "updated" ) :
            raise HTTPException( status_code=404, detail=result.get( "error", "Task not found" ) )
        return {"status" : "success", "result" : result}
    except HTTPException :
        raise
    except Exception as e :
        raise HTTPException( status_code=500, detail=str( e ) )


# ============================================================================
# PROGRESS TRACKER — PROJECTS
# ============================================================================

@app.post( "/progress/projects/add" )
def add_project ( request: ProjectAddRequest ) :
    try :
        project = get_progress_tracker().add_project( request.user_id, request.project )
        return {"status" : "success", "project" : project}
    except Exception as e :
        raise HTTPException( status_code=500, detail=str( e ) )


@app.patch( "/progress/projects/update" )
def update_project ( request: ProjectUpdateRequest ) :
    try :
        result = get_progress_tracker().update_project( request.user_id, request.project_id, request.updates )
        if "error" in result :
            raise HTTPException( status_code=404, detail=result["error"] )
        return {"status" : "success", "project" : result}
    except HTTPException :
        raise
    except Exception as e :
        raise HTTPException( status_code=500, detail=str( e ) )


@app.post( "/progress/projects/import" )
def import_projects ( request: RoadmapImportRequest ) :
    try :
        tracker = get_progress_tracker()
        projects = request.roadmap.get( "projects", request.roadmap ) if isinstance( request.roadmap, dict ) else []
        result = tracker.import_projects( request.user_id,
                                          projects if isinstance( projects, list ) else [request.roadmap] )
        return {"status" : "success", **result}
    except Exception as e :
        raise HTTPException( status_code=500, detail=str( e ) )


# ============================================================================
# PROGRESS TRACKER — DSA
# ============================================================================

@app.post( "/progress/dsa/log" )
def log_dsa_problem ( request: DSALogRequest ) :
    try :
        result = get_progress_tracker().log_dsa_problem(
            request.user_id, request.topic, request.problem_name,
            request.difficulty, request.solved
        )
        return {"status" : "success", "topic_progress" : result}
    except Exception as e :
        raise HTTPException( status_code=500, detail=str( e ) )


@app.post( "/progress/dsa/bulk-update" )
def bulk_update_dsa ( request: DSABulkUpdateRequest ) :
    try :
        result = get_progress_tracker().bulk_update_dsa(
            request.user_id, request.topic, request.solved_count
        )
        return {"status" : "success", "topic_progress" : result}
    except Exception as e :
        raise HTTPException( status_code=500, detail=str( e ) )


# ============================================================================
# PROGRESS TRACKER — INTERVIEWS
# ============================================================================

@app.post( "/progress/interviews/add" )
def add_interview ( request: InterviewAddRequest ) :
    try :
        interview = get_progress_tracker().add_interview(
            request.user_id, request.company, request.role, request.source
        )
        return {"status" : "success", "interview" : interview}
    except Exception as e :
        raise HTTPException( status_code=500, detail=str( e ) )


@app.patch( "/progress/interviews/stage" )
def update_interview_stage ( request: InterviewStageUpdateRequest ) :
    try :
        result = get_progress_tracker().update_interview_stage(
            request.user_id, request.interview_id, request.new_stage, request.notes
        )
        if "error" in result :
            raise HTTPException( status_code=404, detail=result["error"] )
        return {"status" : "success", "interview" : result}
    except HTTPException :
        raise
    except Exception as e :
        raise HTTPException( status_code=500, detail=str( e ) )


@app.delete( "/progress/interviews/{user_id}/{interview_id}" )
def delete_interview ( user_id: str, interview_id: str ) :
    try :
        result = get_progress_tracker().delete_interview( user_id, interview_id )
        return {"status" : "success", "deleted" : result.get( "deleted", False )}
    except Exception as e :
        raise HTTPException( status_code=500, detail=str( e ) )


@app.get( "/progress/{user_id}/interviews/analytics" )
def get_interview_analytics ( user_id: str ) :
    try :
        analytics = get_progress_tracker().get_interview_analytics( user_id )
        return {"status" : "success", "analytics" : analytics}
    except Exception as e :
        raise HTTPException( status_code=500, detail=str( e ) )


# ============================================================================
# PROGRESS SUMMARY
# ============================================================================

@app.get( "/progress/{user_id}/summary" )
def get_progress_summary ( user_id: str ) :
    try :
        summary = get_progress_tracker().get_summary( user_id )
        return {"status" : "success", "summary" : summary}
    except Exception as e :
        raise HTTPException( status_code=500, detail=str( e ) )


@app.get( "/progress/{user_id}/full" )
def get_full_progress ( user_id: str ) :
    try :
        tracker = get_progress_tracker()
        state = tracker.get_state( user_id )
        summary = tracker.get_summary( user_id )
        roadmap = tracker.get_roadmap_with_progress( user_id )
        return {
            "status" : "success",
            "user_id" : user_id,
            "summary" : summary,
            "roadmap" : roadmap,
            "projects" : state.get( "projects", [] ),
            "dsa" : state.get( "dsa", {} ),
            "interviews" : state.get( "interviews", [] ),
            "activity_log" : state.get( "activity_log", [] )[-30 :],
        }
    except Exception as e :
        raise HTTPException( status_code=500, detail=str( e ) )


# ============================================================================
# JOB COACH CHATBOT
# ============================================================================

@app.post( "/coach/chat" )
def job_coach_chat ( request: JobCoachRequest ) :
    if not request.messages :
        raise HTTPException( status_code=400, detail="messages list is required" )
    try :
        messages = [{"role" : m.role, "content" : m.content} for m in request.messages]
        reply = get_job_coach().chat( messages=messages, resume_text=request.resume_text )
        return {"status" : "success", "reply" : reply}
    except Exception as e :
        raise HTTPException( status_code=500, detail=str( e ) )


# ============================================================================
# MARKET INSIGHTS
# ============================================================================

@app.post( "/insights/market" )
def market_insights ( request: MarketInsightsRequest ) :
    if not request.role.strip() :
        raise HTTPException( status_code=400, detail="role is required" )
    try :
        result = get_market_insights().get_insights(
            role=request.role, skills=request.skills, location=request.location
        )
        return {"status" : "success", **result}
    except Exception as e :
        raise HTTPException( status_code=500, detail=str( e ) )


# ============================================================================
# INTERVIEW COACH
# ============================================================================

@app.post( "/interview/questions" )
def get_interview_questions ( request: InterviewQuestionsRequest ) :
    if not request.role.strip() :
        raise HTTPException( status_code=400, detail="role is required" )
    try :
        questions = get_interview_coach().generate_questions(
            role=request.role, interview_type=request.interview_type,
            resume_text=request.resume_text, num_questions=request.num_questions
        )
        return {"status" : "success", "questions" : questions}
    except Exception as e :
        raise HTTPException( status_code=500, detail=str( e ) )


@app.post( "/interview/chat" )
def interview_chat ( request: InterviewChatRequest ) :
    if not request.messages :
        raise HTTPException( status_code=400, detail="messages list is required" )
    if not request.role.strip() :
        raise HTTPException( status_code=400, detail="role is required" )
    try :
        messages = [{"role" : m.role, "content" : m.content} for m in request.messages]
        reply = get_interview_coach().chat(
            messages=messages, role=request.role,
            interview_type=request.interview_type, resume_text=request.resume_text
        )
        return {"status" : "success", "reply" : reply}
    except Exception as e :
        raise HTTPException( status_code=500, detail=str( e ) )


@app.post( "/interview/evaluate" )
def evaluate_answer ( request: EvaluateAnswerRequest ) :
    if not request.question.strip() or not request.answer.strip() :
        raise HTTPException( status_code=400, detail="question and answer are required" )
    try :
        feedback = get_interview_coach().evaluate_answer(
            question=request.question, answer=request.answer,
            role=request.role, interview_type=request.interview_type
        )
        return {"status" : "success", "feedback" : feedback}
    except Exception as e :
        raise HTTPException( status_code=500, detail=str( e ) )


# ============================================================================
# RESUME REWRITER
# ============================================================================

@app.post( "/resume/rewrite" )
def rewrite_resume ( request: ResumeRewriteRequest ) :
    if not request.resume_text.strip() :
        raise HTTPException( status_code=400, detail="resume_text is required" )
    if not request.target_role.strip() :
        raise HTTPException( status_code=400, detail="target_role is required" )
    try :
        result = resume_rewriter.rewrite(
            resume_text=request.resume_text,
            target_role=request.target_role,
            tone=request.tone
        )
        return {"status" : "success", "result" : result}
    except Exception as e :
        logger.error( f"Resume rewrite error: {e}", exc_info=True )
        raise HTTPException( status_code=500, detail=str( e ) )


# ============================================================================
# ATS RESUME SCORER
# ============================================================================

@app.post( "/ats/score" )
def score_resume ( request: ATSScoreRequest ) :
    if not request.resume_text.strip() :
        raise HTTPException( status_code=400, detail="resume_text is required" )
    try :
        result = ats_scorer.score_resume(
            resume_text=request.resume_text,
            target_role=request.target_role or "Software Engineer",
            job_description=request.job_description or None,
        )

        # Attach confidence report
        try :
            uh = get_uncertainty_handler()
            result, ats_report = uh.wrap_ats( result )
            result['_confidence'] = ats_report.to_dict()
        except Exception :
            pass

        return {"status" : "success", "result" : result}
    except Exception as e :
        logger.error( f"ATS scoring error: {e}", exc_info=True )
        raise HTTPException( status_code=500, detail=str( e ) )


# ============================================================================
# AI HR RECRUITER PANEL
# ============================================================================

@app.post( "/interview/hr-panel" )
def hr_recruiter_panel ( request: HRRecruiterRequest ) :
    if not request.resume_text.strip() :
        raise HTTPException( status_code=400, detail="resume_text is required" )

    panel = _run_hr_panel(
        resume_text=request.resume_text,
        target_role=request.target_role,
        company_type=request.company_type,
        focus_area=request.focus_area,
        job_description=request.job_description,
    )
    return {"status" : "success", "panel" : panel}


def _fix_json_string_hr ( json_str: str ) -> str :
    """Fix common JSON issues in HR panel responses."""
    import re

    # Remove any BOM characters
    if json_str.startswith( '\ufeff' ) :
        json_str = json_str[1 :]

    # Fix single quotes around property names
    json_str = re.sub( r"([{,])\s*'([^']+)'\s*:", r'\1"\2":', json_str )
    # Fix single quotes around string values
    json_str = re.sub( r':\s*\'([^\']*)\'\s*([,}])', r': "\1"\2', json_str )

    # Remove trailing commas
    json_str = re.sub( r',\s*}', '}', json_str )
    json_str = re.sub( r',\s*]', ']', json_str )

    # Fix missing quotes around property names
    json_str = re.sub( r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str )

    return json_str


def _get_fallback_hr_panel ( target_role: str, company_type: str, focus_area: str,
                             job_description: Optional[str] = None ) -> dict :
    """Return a fallback HR panel structure when API calls fail."""
    import random

    verdicts = ["Maybe", "Yes", "No"]
    verdict = random.choice( verdicts )

    questions = [
        {
            "question" : f"Can you describe your experience with {target_role} responsibilities?",
            "reason" : "To assess practical experience depth",
            "type" : "technical"
        },
        {
            "question" : "Tell me about a challenging project you worked on and how you overcame obstacles.",
            "reason" : "To evaluate problem-solving approach",
            "type" : "behavioural"
        },
        {
            "question" : "Where do you see your career in the next 3-5 years?",
            "reason" : "To understand career alignment and growth potential",
            "type" : "situational"
        }
    ]

    if job_description :
        questions.append( {
            "question" : "How does your experience specifically match the requirements in the job description?",
            "reason" : "To assess fit for this specific role",
            "type" : "technical"
        } )

    return {
        "hire_verdict" : verdict,
        "verdict_confidence" : 65,
        "verdict_summary" : f"Based on available information, the candidate shows {verdict.lower()} potential for the {target_role} position.",
        "dimension_scores" : {
            "technical_fit" : random.randint( 5, 8 ),
            "experience_relevance" : random.randint( 5, 8 ),
            "culture_fit" : random.randint( 6, 9 ),
            "growth_potential" : random.randint( 6, 9 ),
            "communication_clarity" : random.randint( 6, 9 )
        },
        "green_flags" : ["Relevant experience mentioned", "Good communication skills", "Career progression evident"],
        "red_flags" : ["Gaps in specific technical skills", "Could provide more quantifiable achievements"],
        "questions_to_ask" : questions,
        "salary_bracket_inr" : "₹12-18 LPA",
        "suggested_interview_rounds" : ["Initial HR Screen", "Technical Assessment", "Hiring Manager Interview"],
        "recruiter_notes" : "Candidate shows promise but requires deeper technical validation. Recommend proceeding to next round."
    }


def _run_hr_panel (
        resume_text: str,
        target_role: str,
        company_type: str = "startup",
        focus_area: str = "general",
        job_description: Optional[str] = None,
) -> dict :
    """
    Internal helper for HR panel with improved error handling.
    """
    import re as _re, json as _json

    company_context = {
        "startup" : "fast-growing startup (values hustle, breadth, ownership, speed)",
        "mid-size" : "mid-size product company (values depth, process, collaboration)",
        "enterprise" : "large enterprise (values stability, compliance, domain expertise)",
        "faang" : "FAANG/top-tier tech company (values problem-solving, scale, CS fundamentals)",
    }.get( company_type, "tech company" )

    focus_context = {
        "general" : "holistic profile evaluation",
        "technical" : "technical depth, CS fundamentals, system design",
        "behavioural" : "leadership, teamwork, conflict resolution, cultural fit",
        "compensation" : "market value, compensation expectations, negotiation readiness",
    }.get( focus_area, "holistic profile evaluation" )

    jd_section = ""
    jd_note = ""
    if job_description and job_description.strip() :
        jd_section = f"\nJOB DESCRIPTION (evaluate the candidate against THIS, not generic role expectations):\n{job_description[:2000]}\n"
        jd_note = " Reference specific requirements from the Job Description when explaining your verdict and flagging gaps."

    prompt = f"""You are a senior HR recruiter at a {company_context}.
You are screening a candidate for the role: "{target_role}"
Focus area for this evaluation: {focus_context}{jd_note}
{jd_section}
RESUME:
{resume_text[:2500]}

Produce a JSON hiring assessment. Return ONLY valid JSON, no markdown:
{{
  "hire_verdict": "<Strong Yes | Yes | Maybe | No | Strong No>",
  "verdict_confidence": <integer 0-100>,
  "verdict_summary": "<2-3 sentences explaining the decision{' referencing JD requirements' if jd_section else ''}>",
  "dimension_scores": {{
    "technical_fit": <0-10>,
    "experience_relevance": <0-10>,
    "culture_fit": <0-10>,
    "growth_potential": <0-10>,
    "communication_clarity": <0-10>
  }},
  "green_flags": ["<positive signal 1>", "<positive signal 2>", "<positive signal 3>"],
  "red_flags": ["<concern 1>", "<concern 2>"],
  "questions_to_ask": [
    {{"question": "<interview question>", "reason": "<why this question matters>", "type": "<technical|behavioural|situational>"}},
    {{"question": "<interview question>", "reason": "<why>", "type": "<type>"}},
    {{"question": "<interview question>", "reason": "<why>", "type": "<type>"}},
    {{"question": "<interview question>", "reason": "<why>", "type": "<type>"}},
    {{"question": "<interview question>", "reason": "<why>", "type": "<type>"}}
  ],
  "salary_bracket_inr": "<e.g. ₹12-16 LPA based on profile>",
  "suggested_interview_rounds": ["<round 1>", "<round 2>", "<round 3>"],
  "recruiter_notes": "<2-3 candid internal notes a recruiter would write>"
}}"""

    try :
        from backend.services.llm import llm_json
        result = llm_json(
            system="You are an expert HR recruiter. Always respond with valid JSON only.",
            user=prompt,
            temp=0.4,
            max_tokens=2000,
        )
        return result
    except _json.JSONDecodeError as e :
        logger.error( f"HR panel JSON parse error: {e}" )
        return _get_fallback_hr_panel( target_role, company_type, focus_area, job_description )
    except Exception as e :
        logger.error( f"HR panel error: {e}" )
        return _get_fallback_hr_panel( target_role, company_type, focus_area, job_description )


# ============================================================================
# COMBINED RESUME ANALYZER  (/resume/analyze)
# ============================================================================

@app.post( "/resume/analyze" )
def analyze_resume ( request: ResumeAnalyzeRequest ) :
    """
    Runs ATS scoring and HR recruiter panel in parallel and returns both results.
    """
    if not request.resume_text.strip() :
        raise HTTPException( status_code=400, detail="resume_text is required" )
    if not request.target_role.strip() :
        raise HTTPException( status_code=400, detail="target_role is required" )

    import concurrent.futures

    ats_result = None
    hr_panel = None
    ats_error = None
    hr_error = None

    def run_ats () :
        return ats_scorer.score_resume(
            resume_text=request.resume_text,
            target_role=request.target_role,
            job_description=request.job_description or None,
        )

    def run_hr () :
        return _run_hr_panel(
            resume_text=request.resume_text,
            target_role=request.target_role,
            company_type=request.company_type,
            focus_area=request.focus_area,
            job_description=request.job_description or None,
        )

    with concurrent.futures.ThreadPoolExecutor( max_workers=2 ) as pool :
        ats_future = pool.submit( run_ats )
        hr_future = pool.submit( run_hr )

        try :
            ats_result = ats_future.result( timeout=60 )
            # Attach confidence report
            try :
                uh = get_uncertainty_handler()
                ats_result, ats_report = uh.wrap_ats( ats_result )
                ats_result["_confidence"] = ats_report.to_dict()
            except Exception :
                pass
        except Exception as e :
            logger.error( f"ATS scoring error in /resume/analyze: {e}" )
            ats_error = str( e )

        try :
            hr_panel = hr_future.result( timeout=60 )
        except Exception as e :
            logger.error( f"HR panel error in /resume/analyze: {e}" )
            hr_error = str( e )

    if ats_result is None and hr_panel is None :
        raise HTTPException(
            status_code=500,
            detail=f"Both analyses failed. ATS: {ats_error}. HR: {hr_error}",
        )

    return {
        "status" : "partial" if (ats_error or hr_error) else "success",
        "ats_result" : ats_result,
        "hr_panel" : hr_panel,
        "ats_error" : ats_error,
        "hr_error" : hr_error,
        "jd_used" : bool( request.job_description and request.job_description.strip() ),
    }


# ============================================================================
# PROGRESS STORE (Legacy — kept for backward compatibility)
# ============================================================================

@app.get( "/progress/dsa" )
def list_dsa_problems ( topic: Optional[str] = None, difficulty: Optional[str] = None,
                        solved: Optional[bool] = None ) :
    problems = progress_store.get_all_dsa()
    if topic :
        problems = [p for p in problems if p.get( "topic" ) == topic]
    if difficulty :
        problems = [p for p in problems if p.get( "difficulty" ) == difficulty]
    if solved is not None :
        problems = [p for p in problems if p.get( "solved" ) == solved]
    return {"status" : "success", "problems" : problems, "count" : len( problems )}


@app.post( "/progress/dsa/add" )
def add_dsa_problem ( problem: DSAProblem ) :
    saved = progress_store.upsert_dsa_problem( problem.dict() )
    return {"status" : "success", "problem" : saved}


@app.patch( "/progress/dsa/update" )
def update_dsa_problem ( update: DSAProgressUpdate ) :
    result = progress_store.update_dsa_progress(
        update.problem_id, update.solved, update.attempts, update.notes
    )
    if not result :
        raise HTTPException( status_code=404, detail="Problem not found" )
    return {"status" : "success", "problem" : result}


@app.patch( "/progress/dsa/bulk-update-legacy" )
def bulk_update_dsa_legacy ( bulk: DSABulkUpdate ) :
    results = []
    for u in bulk.updates :
        r = progress_store.update_dsa_progress( u.problem_id, u.solved, u.attempts, u.notes )
        if r :
            results.append( r )
    return {"status" : "success", "updated" : len( results ), "problems" : results}


# ============================================================================
# TN AUTOMOTIVE
# ============================================================================

@app.post( "/tn/analyze-profile" )
def analyze_tn_profile ( request: TNSkillAnalysisRequest ) :
    extracted = tn_extractor.extract_skills( request.profile_text )
    result = {"extracted_skills" : extracted, "total_skills_found" : len( extracted ),
              "nsqf_summary" : _build_nsqf_summary( extracted ), "role_analysis" : None}
    if request.target_role :
        result["role_analysis"] = tn_extractor.get_skill_gaps_for_role( extracted, request.target_role )
    return result


@app.post( "/tn/batch-analytics" )
def batch_analytics ( request: BatchAnalysisRequest ) :
    if not request.profiles :
        raise HTTPException( status_code=400, detail="No profiles provided" )
    if len( request.profiles ) > 500 :
        raise HTTPException( status_code=400, detail="Maximum 500 profiles per batch" )
    logger.info( f"Batch analytics: {len( request.profiles )} profiles — '{request.institution_name}'" )
    analytics = tn_extractor.batch_analyze( [p.dict() for p in request.profiles] )
    return {"institution" : request.institution_name, "status" : "success", **analytics}


@app.get( "/tn/roles" )
def list_tn_roles () :
    return {"roles" : [
        {"role" : name, "description" : d["description"], "cluster" : d["cluster"],
         "nsqf_target" : d["nsqf_target"],
         "nsqf_target_label" : NSQF_LEVELS[d["nsqf_target"]]["label"],
         "required_skills" : d["required_skills"], "preferred_skills" : d["preferred_skills"],
         "typical_employers" : d["typical_employer"]}
        for name, d in tn_extractor.job_roles.items()
    ]}


@app.get( "/tn/skills" )
def list_tn_skills () :
    return {"total_skills" : len( TN_SKILL_DB ), "skills" : [
        {"skill" : s["skill"], "category" : s["category"], "sector" : s["sector"],
         "nsqf_level" : s["nsqf_level"], "nsqf_label" : NSQF_LEVELS[s["nsqf_level"]]["label"],
         "training_sources" : s["training_src"]}
        for s in TN_SKILL_DB
    ], "nsqf_levels" : NSQF_LEVELS}


# ============================================================================
# MENTOR ENDPOINTS
# ============================================================================

@app.get( "/mentors/search" )
def search_mentors (
        expertise: Optional[str] = None,
        industry: Optional[str] = None,
        language: Optional[str] = None,
        max_rate: Optional[float] = None,
        min_rating: float = 4.0,
        country: Optional[str] = None,
        available_now: bool = False
) :
    try :
        expertise_list = expertise.split( "," ) if expertise else None
        mentors = get_mentor_service().search_mentors(
            expertise=expertise_list, industry=industry, language=language,
            max_rate=max_rate, min_rating=min_rating, country=country,
            available_now=available_now
        )
        return {"status" : "success", "count" : len( mentors ), "mentors" : mentors}
    except Exception as e :
        raise HTTPException( status_code=500, detail=str( e ) )


@app.post( "/mentors/search" )
def search_mentors_post ( request: MentorSearchRequest ) :
    try :
        mentors = get_mentor_service().search_mentors(
            expertise=request.expertise, industry=request.industry,
            language=request.language, max_rate=request.max_rate,
            min_rating=request.min_rating, country=request.country,
            available_now=request.available_now
        )
        return {"status" : "success", "count" : len( mentors ), "mentors" : mentors}
    except Exception as e :
        raise HTTPException( status_code=500, detail=str( e ) )


@app.get( "/mentors/{mentor_id}" )
def get_mentor ( mentor_id: str ) :
    mentor = get_mentor_service().get_mentor_by_id( mentor_id )
    if not mentor :
        raise HTTPException( status_code=404, detail="Mentor not found" )
    reviews = get_mentor_service().get_mentor_reviews( mentor_id )
    return {"status" : "success", "mentor" : {**mentor, "reviews" : reviews}}


@app.get( "/mentors/{mentor_id}/slots" )
def get_mentor_slots ( mentor_id: str, date: str ) :
    slots = get_mentor_service().get_available_slots( mentor_id, date )
    return {"status" : "success", "date" : date, "available_slots" : slots}


@app.post( "/mentors/book" )
def book_session ( request: BookSessionRequest ) :
    try :
        session = get_mentor_service().book_session(
            user_id=request.user_id, mentor_id=request.mentor_id,
            session_date=request.session_date, session_time=request.session_time,
            duration_hours=request.duration_hours, topic=request.topic, notes=request.notes
        )
        if "error" in session :
            raise HTTPException( status_code=400, detail=session["error"] )
        return {"status" : "success", "session" : session}
    except HTTPException :
        raise
    except Exception as e :
        raise HTTPException( status_code=500, detail=str( e ) )


@app.get( "/mentors/sessions/{user_id}" )
def get_user_sessions ( user_id: str ) :
    sessions = get_mentor_service().get_user_sessions( user_id )
    return {"status" : "success", "count" : len( sessions ), "sessions" : sessions}


@app.post( "/mentors/sessions/{session_id}/cancel" )
def cancel_session ( session_id: str, user_id: str ) :
    result = get_mentor_service().cancel_session( session_id, user_id )
    if "error" in result :
        raise HTTPException( status_code=400, detail=result["error"] )
    return {"status" : "success", "session" : result["session"]}


@app.post( "/mentors/sessions/feedback" )
def session_feedback ( request: SessionFeedbackRequest ) :
    result = get_mentor_service().complete_session(
        session_id=request.session_id, user_id=request.user_id,
        rating=request.rating, feedback=request.feedback
    )
    if "error" in result :
        raise HTTPException( status_code=400, detail=result["error"] )
    return {"status" : "success", "session" : result["session"]}


@app.get( "/mentors/industries" )
def get_industries () :
    service = get_mentor_service()
    industries = set()
    for mentor in service.mentors :
        industries.update( mentor['industries'] )
    return {"status" : "success", "industries" : sorted( list( industries ) )}


@app.get( "/mentors/languages" )
def get_languages () :
    service = get_mentor_service()
    languages = set()
    for mentor in service.mentors :
        languages.update( mentor['languages_spoken'] )
    return {"status" : "success", "languages" : sorted( list( languages ) )}


# ============================================================================
# STATS & HEALTH
# ============================================================================

@app.get( "/rag/stats" )
def get_stats () :
    return vector_store.get_stats()


@app.get( "/health" )
def health_check () :
    errors = settings.validate()

    # Check new services
    try :
        fe_ok = bool( get_feedback_engine() )
    except Exception :
        fe_ok = False
        errors.append( "feedback_engine: failed to initialize" )

    try :
        ltr_ok = bool( get_ltr_engine() )
    except Exception :
        ltr_ok = False
        errors.append( "learning_to_rank: failed to initialize" )

    return {
        "status" : "healthy" if not errors else "degraded",
        "errors" : errors,
        "vector_db_jobs" : vector_store.collection.count(),
        "vector_db_freshness" : vector_store.get_stats().get( "freshness", "unknown" ),
        "services" : {
            "vector_store" : "ok",
            "job_scraper" : "ok" if settings.SERPAPI_KEY else "missing_api_key",
            "career_advisor" : "ok" if career_advisor else "not_initialized",
            "groq_llm" : "ok" if settings.GROQ_API_KEY else "missing_api_key",
            "anthropic_llm" : "ok" if settings.ANTHROPIC_API_KEY else "missing_api_key",
            "gemini_llm" : "ok (tertiary)" if settings.GEMINI_API_KEY else "not configured (optional)",
            "job_coach" : "ok" if (settings.GROQ_API_KEY or settings.ANTHROPIC_API_KEY) else "missing_api_key",
            "market_insights" : "ok" if (settings.GROQ_API_KEY or settings.ANTHROPIC_API_KEY) else "missing_api_key",
            "interview_coach" : "ok" if (settings.GROQ_API_KEY or settings.ANTHROPIC_API_KEY) else "missing_api_key",
            "progress_tracker" : "ok",
            "resume_rewriter" : "ok" if resume_rewriter else "not_initialized",
            "tn_automotive_taxonomy" : f"ok — {len( tn_extractor.skill_db )} skills",
            "feedback_engine" : "ok" if fe_ok else "failed",
            "learning_to_rank" : "ok" if ltr_ok else "failed",
            "agent_orchestrator" : "ok" if (settings.GROQ_API_KEY or settings.ANTHROPIC_API_KEY) else "missing_api_key",
            "agent_debate" : "ok" if (settings.GROQ_API_KEY or settings.ANTHROPIC_API_KEY) else "missing_api_key",
        }
    }


# ============================================================================
# GOD-MODE /ask  — Full async multi-agent pipeline
# ============================================================================

class AskRequest( BaseModel ) :
    query: str
    session_id: str = "default"
    resume_text: Optional[str] = None
    target_role: Optional[str] = None
    location: str = "India"


@app.post( "/ask" )
async def ask ( request: AskRequest ) :
    import asyncio as _asyncio

    try :
        from backend.services.llm import llm_call, llm_call_smart
        from backend.services.state_manager import state
        from backend.services.scoring import weighted_vote, score_responses
        from backend.services.confidence import estimate_confidence
        from backend.services.consistency import check_consistency
        from backend.services.retriever import retrieve_context
        from backend.services.job_tool import get_job_summary
        from backend.services.skill_tool import extract_skills_fast
    except ImportError as e :
        logger.error( f"/ask import error: {e}" )
        raise HTTPException( status_code=500, detail=f"Module import failed: {e}" )

    query = request.query.strip()
    session_id = request.session_id
    resume = request.resume_text or state.resume( session_id )
    role = request.target_role or state.target_role( session_id ) or "Software Engineer"

    if not query :
        raise HTTPException( status_code=400, detail="query is required" )

    # Session state
    session = state.get( session_id )
    if resume :
        state.set_resume( session_id, resume, role )

    history_ctx = ""
    recent = state.history( session_id, last_n=3 )
    if recent :
        history_ctx = "Recent conversation:\n" + "\n".join(
            f"Q: {h['query']}\nA: {h['final'][:120]}…" for h in recent
        )

    # RAG retrieval
    rag_context = retrieve_context( query, top_k=3 )

    # Tool calls (parallel)
    loop = _asyncio.get_event_loop()

    def _jobs_tool () :
        return get_job_summary( role, location=request.location, top_n=3 )

    def _skills_tool () :
        if not resume :
            return ""
        skills = extract_skills_fast( resume )
        return f"Candidate skills: {', '.join( skills[:12] )}" if skills else ""

    jobs_ctx, skills_ctx = await _asyncio.gather(
        loop.run_in_executor( None, _jobs_tool ),
        loop.run_in_executor( None, _skills_tool ),
    )

    # Build shared context block
    context_block = "\n\n".join( filter( None, [
        rag_context,
        jobs_ctx,
        skills_ctx,
        history_ctx,
    ] ) )

    # Parallel proposer agents
    PROPOSERS = {
        "Optimist" : "You maximise opportunity and growth. Be ambitious but grounded.",
        "Realist" : "You focus on feasibility, market realities, and practical constraints.",
        "Market" : "You specialise in hiring trends, salary data, and in-demand skills.",
    }

    async def _propose ( agent_name: str, agent_role: str ) -> Tuple[str, str] :
        system = (
            f"You are a career advisor. Role: {agent_role}\n"
            f"Target role being considered: {role}\n"
            "Think step-by-step and give a specific, actionable answer."
        )
        user = (
            f"Context:\n{context_block}\n\n"
            f"Question: {query}"
        )
        response = await llm_call( system, user, temp=0.7 )
        return agent_name, response

    proposal_tasks = [_propose( name, role_desc ) for name, role_desc in PROPOSERS.items()]
    proposal_pairs = await _asyncio.gather( *proposal_tasks )
    responses: Dict[str, str] = {name : resp for name, resp in proposal_pairs}

    logger.info( f"[/ask] {len( responses )} proposer responses collected" )

    # Critic agent
    responses_text = "\n\n".join( f"[{k}]:\n{v}" for k, v in responses.items() )
    critique = await llm_call(
        system="You are a harsh, precise critic. Identify the weakest claims, "
               "unsupported assumptions, and missing specifics in these responses.",
        user=f"Original question: {query}\n\nResponses:\n{responses_text}",
        temp=0.3,
    )

    # Voting + scoring
    scores, winner = weighted_vote( query, responses )
    logger.info( f"[/ask] Scores: {scores} | Winner: {winner}" )

    # Synthesizer
    final_answer = await llm_call_smart(
        system="You are an expert synthesiser. Combine the best elements of multiple "
               "expert responses into one clear, actionable, specific answer. "
               "Address the critique's concerns. Do not repeat weaknesses.",
        user=(
            f"Original question: {query}\n\n"
            f"Expert responses:\n{responses_text}\n\n"
            f"Critic's analysis:\n{critique}\n\n"
            f"Agent relevance scores: {scores}\n\n"
            f"Produce the definitive best answer:"
        ),
        temp=0.5,
        max_tokens=1500,
    )

    # Confidence estimation
    confidence_report = estimate_confidence( scores, final_answer )

    # Self-consistency check
    consistency_report = check_consistency( responses )

    # Session memory update
    state.update( session_id, {
        "query" : query,
        "final" : final_answer,
        "confidence" : confidence_report["score"],
        "winner_agent" : winner,
    } )

    return {
        "status" : "success",
        "final" : final_answer,
        "responses" : responses,
        "critique" : critique,
        "scores" : scores,
        "winner" : winner,
        "confidence" : confidence_report,
        "consistency" : consistency_report,
        "session" : {
            "id" : session_id,
            "history_count" : len( session.get( "history", [] ) ),
        },
        "context_sources" : {
            "rag_docs_retrieved" : bool( rag_context ),
            "jobs_retrieved" : bool( jobs_ctx ),
            "skills_extracted" : bool( skills_ctx ),
        },
    }


@app.get( "/session/{session_id}" )
def get_session ( session_id: str ) :
    try :
        from backend.services.state_manager import state
        return {"status" : "success", "session" : state.snapshot( session_id )}
    except Exception as e :
        raise HTTPException( status_code=500, detail=str( e ) )


@app.delete( "/session/{session_id}" )
def clear_session ( session_id: str ) :
    try :
        from backend.services.state_manager import state
        state.drop( session_id )
        return {"status" : "success", "message" : f"Session {session_id} cleared."}
    except Exception as e :
        raise HTTPException( status_code=500, detail=str( e ) )


def _build_nsqf_summary ( extracted_skills: List[Dict] ) -> Dict :
    if not extracted_skills :
        return {"peak_level" : 1, "peak_label" : NSQF_LEVELS[1]["label"], "distribution" : {}}
    dist: Dict[int, List] = {}
    for s in extracted_skills :
        dist.setdefault( s["nsqf_level"], [] ).append( s["skill"] )
    peak = max( dist.keys() )
    return {"peak_level" : peak, "peak_label" : NSQF_LEVELS[peak]["label"],
            "distribution" : {NSQF_LEVELS[lvl]["label"] : skills for lvl, skills in sorted( dist.items() )}}

if __name__ == "__main__" :
    import uvicorn

    uvicorn.run( "backend.main:app", host="0.0.0.0", port=8000, reload=True )