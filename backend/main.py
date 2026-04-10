"""
Career Genie AI - Main FastAPI Application
===========================================
A comprehensive career development platform with:
- Resume parsing and ATS scoring
- Job matching and market insights
- AI-powered interview coaching
- Personalized career roadmaps
- Multi-agent debate system for career advice
- Real-time WebRTC mentor sessions
"""

from __future__ import annotations

import json
import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# LIFESPAN MANAGER
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🚀 Career Genie AI API starting up...")

    # Initialize services
    try:
        from backend.services.vector_store import vector_store
        stats = vector_store.get_stats()
        logger.info(f"📚 Vector store ready: {stats['total_jobs']} jobs indexed")
    except Exception as e:
        logger.warning(f"⚠️ Vector store initialization warning: {e}")

    try:
        from backend.services.ollama_service import get_ollama_service
        ollama = get_ollama_service()
        if ollama.available:
            logger.info(f"🤖 Ollama service ready (LLM: {ollama.llm_model})")
        else:
            logger.warning("⚠️ Ollama service not available - run 'ollama serve'")
    except Exception as e:
        logger.warning(f"⚠️ Ollama service warning: {e}")

    try:
        from backend.services.job_scraper import get_job_scraper
        logger.info("🔍 Job scraper service ready")
    except Exception as e:
        logger.warning(f"⚠️ Job scraper warning: {e}")

    logger.info("✅ Career Genie AI API ready!")

    yield

    logger.info("👋 Career Genie AI API shutting down...")


# ─────────────────────────────────────────────────────────────────────────────
# FASTAPI APP
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Career Genie AI API",
    description="AI-powered career development platform",
    version="3.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "https://*.netlify.app",  # Allow all Netlify frontends
        "https://*.ngrok-free.app",  # Allow all ngrok URLs
        "*"  # Temporarily allow all for testing
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# ROUTER IMPORTS
# ─────────────────────────────────────────────────────────────────────────────

from backend.routes.interview_live import router as interview_live_router
app.include_router(interview_live_router)


# ─────────────────────────────────────────────────────────────────────────────
# REQUEST/RESPONSE MODELS
# ─────────────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    resume_text: Optional[str] = None
    session_id: Optional[str] = None


class MatchRequest(BaseModel):
    resume_text: str
    job_query: Optional[str] = None
    top_k: int = 10
    num_jobs: int = 50
    location: str = "India"
    user_id: Optional[str] = None
    min_match_score: float = 40.0
    experience_level: Optional[str] = None
    posted_within_days: Optional[int] = 14
    exclude_remote: bool = False
    force_refresh: bool = False


class RoadmapRequest(BaseModel):
    resume_text: str
    target_role: str
    skill_gaps: Optional[List[str]] = None
    duration_weeks: int = 12


class ATSRequest(BaseModel):
    resume_text: str
    target_role: str = "Software Engineer"
    job_description: Optional[str] = None


class InterviewRequest(BaseModel):
    role: str
    interview_type: str = "mixed"
    resume_text: Optional[str] = None
    num_questions: int = 10


class InterviewAnswerRequest(BaseModel):
    question: str
    answer: str
    role: str
    interview_type: str = "mixed"


class ProgressUpdateRequest(BaseModel):
    task_id: str
    done: bool
    week_key: str


class FeedbackRequest(BaseModel):
    signal_type: str
    item_id: str
    metadata: Optional[Dict] = None


class DebateRequest(BaseModel):
    topic: str
    context: Dict
    max_rounds: int = 2


# ─────────────────────────────────────────────────────────────────────────────
# HEALTH AND CONFIG ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "name": "Career Genie AI API",
        "version": "3.0.0",
        "status": "operational",
        "endpoints": {
            "resume": "/upload-resume/parse",
            "ats": "/ats/score",
            "match": "/rag/match-realtime",
            "roadmap": "/roadmap/generate",
            "interview": "/interview/generate-questions",
            "coach": "/job-coach/chat",
            "debate": "/debate/run",
            "progress": "/progress/*",
        }
    }


@app.get("/config")
async def get_config():
    """Return frontend configuration."""
    return {
        "ollama_available": _check_ollama(),
        "features": {
            "debate": True,
            "live_interview": True,
            "mentor_matching": True,
            "progress_tracking": True,
        }
    }


def _check_ollama() -> bool:
    try:
        from backend.services.ollama_service import get_ollama_service
        return get_ollama_service().available
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# RESUME ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/upload-resume/parse")
async def parse_resume(file: UploadFile = File(...)):
    """Parse uploaded resume file (PDF or DOCX)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Save temporarily
    temp_path = Path(f"/tmp/{uuid.uuid4()}{Path(file.filename).suffix}")
    try:
        content = await file.read()
        temp_path.write_bytes(content)

        from backend.services.resume_parser import resume_parser
        result = resume_parser.parse(str(temp_path))

        # Add uncertainty validation
        from backend.services.uncertainty_handler import get_uncertainty_handler
        uh = get_uncertainty_handler()
        _, report = uh.wrap_parse(result["resume_text"], result["word_count"])

        return {
            "success": True,
            "resume_text": result["resume_text"],
            "word_count": result["word_count"],
            "confidence": report.to_dict(),
        }
    except Exception as e:
        logger.error(f"Resume parse error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path.exists():
            temp_path.unlink()


# ─────────────────────────────────────────────────────────────────────────────
# ATS SCORING ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/ats/score")
async def ats_score(request: ATSRequest):
    """Score resume against target role or job description."""
    try:
        from backend.services.ats_scorer import ats_scorer
        result = ats_scorer.score_resume(
            request.resume_text,
            request.target_role,
            request.job_description
        )

        # Add uncertainty validation
        from backend.services.uncertainty_handler import get_uncertainty_handler
        uh = get_uncertainty_handler()
        _, report = uh.wrap_ats(result)

        return {
            "result": result,              # frontend reads data.result
            "_confidence": report.to_dict() if hasattr(report, "to_dict") else {},
        }
    except Exception as e:
        logger.error(f"ATS score error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# JOB MATCHING ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/rag/match-realtime")
async def match_realtime(request: MatchRequest):
    """Match resume to jobs in real-time."""
    try:
        from backend.services.matcher import get_job_matcher
        matcher = get_job_matcher()

        # Ensure job index is populated — use job_query if provided, else infer from resume
        from backend.services.vector_store import vector_store
        stats_before = vector_store.get_stats()
        if stats_before["total_jobs"] < 10 or request.force_refresh:
            await _refresh_jobs(
                request.resume_text,
                request.location,
                job_query=request.job_query,
                num_jobs=request.num_jobs,
            )

        stats_after = vector_store.get_stats()

        matches = matcher.match_resume_to_jobs(
            request.resume_text,
            top_k=request.top_k,
            location=request.location,
            user_id=request.user_id,
            force_refresh=request.force_refresh,
        )

        # Filter by min_match_score
        matches = [m for m in matches if m.get("match_score", 0) >= request.min_match_score]

        # Add uncertainty validation
        from backend.services.uncertainty_handler import get_uncertainty_handler
        uh = get_uncertainty_handler()
        validated_matches, report = uh.wrap_matches(matches)

        # Attach _confidence to each job so JobCard can display it
        for job in validated_matches:
            if "_confidence" not in job:
                job["_confidence"] = None

        # Get career advice with context
        from backend.services.career_advisor import career_advisor
        advice = career_advisor.generate_career_advice(
            resume_text=request.resume_text,
            target_role=matcher._extract_target_role(request.resume_text),
            job_matches=validated_matches,
        )

        # Build skill_comparison for SkillAssessmentDashboard
        from backend.services.enhanced_skill_extractor import EnhancedSkillExtractor
        extractor = EnhancedSkillExtractor()
        resume_skills = extractor.extract_skills_with_context(request.resume_text)
        skill_comparison = {
            "resume_skills": resume_skills,
            "job_skills": [],
        }

        # Return shape expected by the frontend JobMatches component
        return {
            "matched_jobs": validated_matches,           # frontend reads data.matched_jobs
            "total_jobs_fetched": stats_after.get("total_jobs", len(validated_matches)),
            "total_jobs_indexed": stats_after.get("total_jobs", len(validated_matches)),
            "search_query": request.job_query or "",
            "career_advice": advice,
            "skill_comparison": skill_comparison,
            "_confidence": report.to_dict() if hasattr(report, "to_dict") else {},
        }
    except Exception as e:
        logger.error(f"Match error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _refresh_jobs(resume_text: str, location: str, job_query: str = None, num_jobs: int = 50):
    """Refresh job index in background."""
    try:
        from backend.services.job_scraper import get_job_scraper
        from backend.services.vector_store import vector_store
        from backend.services.matcher import get_job_matcher

        matcher = get_job_matcher()
        # Use the explicit query if provided, otherwise infer from resume
        target_role = job_query.strip() if job_query else matcher._extract_target_role(resume_text)

        scraper = get_job_scraper()
        jobs = scraper.fetch_jobs(query=target_role, location=location, num_jobs=num_jobs)

        if jobs:
            vector_store.index_jobs(jobs)
            logger.info(f"Refreshed {len(jobs)} jobs for query='{target_role}'")
    except Exception as e:
        logger.error(f"Job refresh failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# ROADMAP ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/roadmap/generate")
async def generate_roadmap(request: RoadmapRequest):
    """Generate personalized learning roadmap."""
    try:
        from backend.services.roadmap_generator import get_roadmap_generator
        from backend.services.enhanced_skill_extractor import EnhancedSkillExtractor

        # Extract skills if gaps not provided
        skill_gaps = request.skill_gaps
        if not skill_gaps:
            extractor = EnhancedSkillExtractor()
            skills = extractor.extract_skills_with_context(request.resume_text)
            # Simulate gaps based on target role
            skill_gaps = [s["skill"] for s in skills[:5]] if skills else ["Python", "SQL", "System Design"]

        generator = get_roadmap_generator()
        roadmap = generator.generate_roadmap(
            request.resume_text,
            request.target_role,
            skill_gaps,
            request.duration_weeks,
        )

        # Add uncertainty validation
        from backend.services.uncertainty_handler import get_uncertainty_handler
        uh = get_uncertainty_handler()
        _, report = uh.wrap_roadmap(roadmap)

        return {
            "roadmap": roadmap,
            "_confidence": report.to_dict(),
        }
    except Exception as e:
        logger.error(f"Roadmap generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# INTERVIEW COACH ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/interview/generate-questions")
async def interview_questions(request: InterviewRequest):
    """Generate interview questions for a role."""
    try:
        from backend.services.interview_coach import get_interview_coach
        coach = get_interview_coach()

        questions = coach.generate_questions(
            role=request.role,
            interview_type=request.interview_type,
            resume_text=request.resume_text,
            num_questions=request.num_questions,
        )

        return {"questions": questions}
    except Exception as e:
        logger.error(f"Question generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/interview/evaluate-answer")
async def evaluate_answer(request: InterviewAnswerRequest):
    """Evaluate an interview answer."""
    try:
        from backend.services.interview_coach import get_interview_coach
        coach = get_interview_coach()

        result = coach.evaluate_answer(
            question=request.question,
            answer=request.answer,
            role=request.role,
            interview_type=request.interview_type,
        )

        return result
    except Exception as e:
        logger.error(f"Answer evaluation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# JOB COACH (CHAT) ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/coach/chat")       # alias used by the frontend
@app.post("/job-coach/chat")  # original route kept for backwards compatibility
async def job_coach_chat(request: ChatRequest):
    """Chat with the AI career coach."""
    try:
        from backend.services.job_coach import get_job_coach
        coach = get_job_coach()

        response = coach.chat(
            messages=request.messages,
            resume_text=request.resume_text,
        )

        # Store session if session_id provided
        if request.session_id:
            from backend.services.state_manager import state
            state.update(request.session_id, {
                "query": request.messages[-1]["content"] if request.messages else "",
                "final": response,
                "confidence": 0.8,
            })

        return {
            "reply": response,       # frontend reads data.reply
            "response": response,    # keep for backwards compatibility
        }
    except Exception as e:
        logger.error(f"Job coach error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# DEBATE SYSTEM ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/debate/run")
async def debate_run(request: DebateRequest):
    """Run multi-agent debate for career recommendations."""
    try:
        from backend.services.agent_debate import get_debate_orchestrator
        debate = get_debate_orchestrator()

        result = debate.run_debate(
            topic=request.topic,
            context=request.context,
            max_rounds=request.max_rounds,
        )

        return debate.to_dict(result)
    except Exception as e:
        logger.error(f"Debate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/debate/quick-critique")
async def quick_critique(plan: Dict, context: Dict):
    """Quick single-round critique of a plan."""
    try:
        from backend.services.agent_debate import get_debate_orchestrator
        debate = get_debate_orchestrator()

        result = debate.quick_critique(plan, context)
        return result
    except Exception as e:
        logger.error(f"Critique error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# PROGRESS TRACKING ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

class ImportRoadmapBody(BaseModel):
    user_id: str
    roadmap: Dict

class ImportProjectsBody(BaseModel):
    user_id: str
    projects: List[Dict]

class TaskUpdateBody(BaseModel):
    user_id: str
    week_key: str
    task_id: str
    done: bool

class ProjectUpdateBody(BaseModel):
    user_id: str
    project_id: str
    updates: Optional[Dict] = None
    status: Optional[str] = None
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    progress_pct: Optional[int] = None
    notes: Optional[str] = None

class DSABulkUpdateBody(BaseModel):
    user_id: str
    topic: str
    solved_count: int

class InterviewAddBody(BaseModel):
    user_id: str
    company: str
    role: str
    source: str = "LinkedIn"

class InterviewStageBody(BaseModel):
    user_id: str
    interview_id: str
    new_stage: str
    notes: str = ""


# ── GET summary / full / analytics ──────────────────────────────────────────

@app.get("/progress/{user_id}/summary")
@app.get("/progress/{user_id}")
async def get_progress_summary(user_id: str):
    """Get user progress summary."""
    try:
        from backend.services.progress_tracker import get_progress_tracker
        tracker = get_progress_tracker()
        return tracker.get_summary(user_id)
    except Exception as e:
        logger.error(f"Progress summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/progress/{user_id}/full")
async def get_progress_full(user_id: str):
    """Get full user progress state (roadmap weeks, projects, DSA, interviews)."""
    try:
        from backend.services.progress_tracker import get_progress_tracker
        tracker = get_progress_tracker()
        # Return full state; fall back to summary if tracker doesn't have get_full
        if hasattr(tracker, "get_full"):
            return tracker.get_full(user_id)
        return tracker.get_summary(user_id)
    except Exception as e:
        logger.error(f"Progress full error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/progress/{user_id}/interviews/analytics")
async def get_interview_analytics(user_id: str):
    """Get interview pipeline analytics."""
    try:
        from backend.services.progress_tracker import get_progress_tracker
        tracker = get_progress_tracker()
        if hasattr(tracker, "get_interview_analytics"):
            return tracker.get_interview_analytics(user_id)
        summary = tracker.get_summary(user_id)
        return {"interviews": summary.get("interviews", [])}
    except Exception as e:
        logger.error(f"Interview analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Roadmap ──────────────────────────────────────────────────────────────────

@app.post("/progress/roadmap/import")
async def import_roadmap(body: ImportRoadmapBody):
    """Import roadmap for user."""
    try:
        from backend.services.progress_tracker import get_progress_tracker
        tracker = get_progress_tracker()
        return tracker.import_roadmap(body.user_id, body.roadmap)
    except Exception as e:
        logger.error(f"Roadmap import error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/progress/roadmap/task/update")   # frontend path
@app.post("/progress/task/update")           # original path
async def update_task(body: TaskUpdateBody):
    """Update task completion status."""
    try:
        from backend.services.progress_tracker import get_progress_tracker
        tracker = get_progress_tracker()
        return tracker.update_task(body.user_id, body.week_key, body.task_id, body.done)
    except Exception as e:
        logger.error(f"Task update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Projects ─────────────────────────────────────────────────────────────────

@app.post("/progress/projects/import")
async def import_projects(body: ImportProjectsBody):
    """Import project suggestions into user's tracker."""
    try:
        from backend.services.progress_tracker import get_progress_tracker
        tracker = get_progress_tracker()
        if hasattr(tracker, "import_projects"):
            return tracker.import_projects(body.user_id, body.projects)
        return {"status": "ok", "imported": len(body.projects)}
    except Exception as e:
        logger.error(f"Projects import error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/progress/projects/update")
async def update_project(body: ProjectUpdateBody):
    """Update a project entry."""
    try:
        from backend.services.progress_tracker import get_progress_tracker
        tracker = get_progress_tracker()
        updates = body.updates or {
            k: v for k, v in {
                "status": body.status,
                "github_url": body.github_url,
                "live_url": body.live_url,
                "progress_pct": body.progress_pct,
                "notes": body.notes,
            }.items() if v is not None
        }
        if hasattr(tracker, "update_project"):
            return tracker.update_project(body.user_id, body.project_id, updates)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Project update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── DSA ───────────────────────────────────────────────────────────────────────

@app.post("/progress/dsa/bulk-update")   # frontend path
@app.post("/progress/dsa/log")           # original path
async def bulk_update_dsa(body: DSABulkUpdateBody):
    """Bulk-update DSA solved count for a topic."""
    try:
        from backend.services.progress_tracker import get_progress_tracker
        tracker = get_progress_tracker()
        if hasattr(tracker, "bulk_update_dsa"):
            return tracker.bulk_update_dsa(body.user_id, body.topic, body.solved_count)
        # Fallback: log N problems
        for i in range(body.solved_count):
            tracker.log_dsa_problem(body.user_id, body.topic, f"problem_{i+1}", "medium", True)
        return {"status": "ok", "logged": body.solved_count}
    except Exception as e:
        logger.error(f"DSA bulk update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Interviews ────────────────────────────────────────────────────────────────

@app.post("/progress/interviews/add")   # frontend path
@app.post("/progress/interview/add")    # original path
async def add_interview(body: InterviewAddBody):
    """Add job application/interview entry."""
    try:
        from backend.services.progress_tracker import get_progress_tracker
        tracker = get_progress_tracker()
        return tracker.add_interview(body.user_id, body.company, body.role, body.source)
    except Exception as e:
        logger.error(f"Interview add error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/progress/interviews/stage")
async def update_interview_stage(body: InterviewStageBody):
    """Update interview pipeline stage."""
    try:
        from backend.services.progress_tracker import get_progress_tracker
        tracker = get_progress_tracker()
        if hasattr(tracker, "update_interview_stage"):
            return tracker.update_interview_stage(body.user_id, body.interview_id, body.new_stage, body.notes)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Interview stage update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/progress/interviews/{user_id}/{interview_id}")
async def delete_interview(user_id: str, interview_id: str):
    """Delete an interview entry."""
    try:
        from backend.services.progress_tracker import get_progress_tracker
        tracker = get_progress_tracker()
        if hasattr(tracker, "delete_interview"):
            return tracker.delete_interview(user_id, interview_id)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Interview delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# FEEDBACK ENGINE ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

class FeedbackBody(BaseModel):
    user_id: str
    signal_type: str
    item_id: str
    metadata: Optional[Dict] = None


@app.post("/feedback/record")
async def record_feedback(body: FeedbackBody):
    """Record user feedback signal."""
    try:
        from backend.services.feedback_engine import get_feedback_engine
        engine = get_feedback_engine()

        weights = engine.record(
            user_id=body.user_id,
            signal_type=body.signal_type,
            item_id=body.item_id,
            metadata=body.metadata,
        )

        return {"weights": weights}
    except Exception as e:
        logger.error(f"Feedback record error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/feedback/stats/{user_id}")
async def feedback_stats(user_id: str):
    """Get feedback statistics for user."""
    try:
        from backend.services.feedback_engine import get_feedback_engine
        engine = get_feedback_engine()

        stats = engine.get_stats(user_id)
        return stats
    except Exception as e:
        logger.error(f"Feedback stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# AGENT ORCHESTRATOR ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/orchestrator/run")
async def orchestrator_run(goal: str, user_id: str = "", extra_context: Optional[Dict] = None):
    """Run the agent orchestrator for a goal."""
    try:
        from backend.services.agent_orchestrator import get_orchestrator
        orchestrator = get_orchestrator()

        result = orchestrator.run_goal(
            goal=goal,
            user_id=user_id,
            extra_context=extra_context,
        )

        return result
    except Exception as e:
        logger.error(f"Orchestrator error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/orchestrator/plan")
async def orchestrator_plan(user_intent: str, user_id: str = ""):
    """Plan tasks from user intent."""
    try:
        from backend.services.agent_orchestrator import get_orchestrator
        orchestrator = get_orchestrator()

        result = orchestrator.plan_from_intent(user_intent, user_id)
        return result
    except Exception as e:
        logger.error(f"Planning error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# MARKET INSIGHTS ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

class MarketInsightsRequest(BaseModel):
    role: str
    skills: Optional[List[str]] = None
    location: str = "India"


@app.post("/insights/market")   # frontend uses POST with JSON body
@app.get("/insights/market")    # keep GET for backwards compatibility
@app.post("/market/insights")
@app.get("/market/insights")
async def market_insights(request: Optional[MarketInsightsRequest] = None,
                          role: Optional[str] = None,
                          skills: Optional[str] = None,
                          location: str = "India"):
    """Get market insights for a role."""
    try:
        from backend.services.market_insights import get_market_insights
        insights = get_market_insights()

        # Support both JSON body (POST) and query params (GET)
        if request is not None:
            _role = request.role
            _skills = request.skills
            _location = request.location
        else:
            _role = role or "Software Engineer"
            _skills = skills.split(",") if skills else None
            _location = location

        result = insights.get_insights(_role, _skills, _location)
        return result
    except Exception as e:
        logger.error(f"Market insights error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# SKILL EXTRACTION ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/skills/extract")
async def extract_skills(text: str, enhanced: bool = True):
    """Extract skills from text."""
    try:
        if enhanced:
            from backend.services.enhanced_skill_extractor import EnhancedSkillExtractor
            extractor = EnhancedSkillExtractor()
            skills = extractor.extract_skills_with_context(text)
        else:
            from backend.services.skill_tool import extract_skills_fast
            skills = extract_skills_fast(text)

        return {"skills": skills}
    except Exception as e:
        logger.error(f"Skill extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/skills/gap")
async def skills_gap(resume_text: str, job_description: str):
    """Compute skill gap between resume and job description."""
    try:
        from backend.services.skill_tool import skills_gap
        result = skills_gap(resume_text, job_description)
        return result
    except Exception as e:
        logger.error(f"Skills gap error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# RESUME REWRITER ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

class ResumeRewriteRequest(BaseModel):
    resume_text: str
    target_role: str = "Software Engineer"
    tone: str = "professional"


@app.post("/resume/rewrite")
async def rewrite_resume(request: ResumeRewriteRequest):
    """Rewrite resume for ATS optimization."""
    try:
        from backend.services.resume_rewriter import resume_rewriter
        result = resume_rewriter.rewrite(request.resume_text, request.target_role, request.tone)
        return {"result": result}      # frontend reads data.result
    except Exception as e:
        logger.error(f"Resume rewrite error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# MENTOR SERVICE ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

class MentorSearchBody(BaseModel):
    query: Optional[str] = None
    domain: Optional[str] = None
    user_skills: Optional[List[str]] = None
    user_id: Optional[str] = None
    expertise: Optional[List[str]] = None
    industry: Optional[str] = None
    language: Optional[str] = None
    max_rate: Optional[float] = None
    min_rating: float = 4.0
    country: Optional[str] = None


class MentorBookBody(BaseModel):
    mentor_id: str
    user_id: str
    date: Optional[str] = None
    time: Optional[str] = None
    session_date: Optional[str] = None
    session_time: Optional[str] = None
    duration_hours: int = 1
    topic: str = ""
    message: str = ""
    notes: str = ""
    mentor_name: Optional[str] = None
    mentor_domain: Optional[str] = None


@app.post("/mentor/search")    # frontend uses POST with JSON body
@app.get("/mentor/search")     # keep GET for backwards compatibility
@app.post("/mentors/search")
@app.get("/mentors/search")
async def search_mentors(body: Optional[MentorSearchBody] = None):
    """Search for mentors."""
    try:
        from backend.services.mentor_service import get_mentor_service
        service = get_mentor_service()

        if body is not None:
            expertise_list = body.expertise or ([body.domain] if body.domain else None)
            results = service.search_mentors(
                expertise=expertise_list,
                industry=body.industry,
                language=body.language,
                max_rate=body.max_rate,
                min_rating=body.min_rating or 4.0,
                country=body.country,
            )
        else:
            results = service.search_mentors()

        # Ensure all results are serializable
        serializable_results = []
        for mentor in results:
            serializable_mentor = {
                "mentor_id": mentor.get("mentor_id", ""),
                "name": mentor.get("name", ""),
                "title": mentor.get("title", ""),
                "company": mentor.get("company", ""),
                "location": mentor.get("location", ""),
                "country": mentor.get("country", ""),
                "timezone": mentor.get("timezone", ""),
                "languages": mentor.get("languages", []),
                "expertise": mentor.get("expertise", []),
                "industries": mentor.get("industries", []),
                "experience_years": mentor.get("experience_years", 0),
                "hourly_rate": mentor.get("hourly_rate", 0),
                "currency": mentor.get("currency", "USD"),
                "bio": mentor.get("bio", ""),
                "available": mentor.get("available", True),
                "rating": mentor.get("rating", 0),
                "total_sessions": mentor.get("total_sessions", 0),
                "languages_spoken": mentor.get("languages_spoken", [])
            }
            serializable_results.append(serializable_mentor)

        return {"mentors": serializable_results}
    except Exception as e:
        logger.error(f"Mentor search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mentor/book")
@app.post("/mentors/book")
async def book_mentor(body: MentorBookBody):
    """Book a mentoring session."""
    try:
        from backend.services.mentor_service import get_mentor_service
        service = get_mentor_service()

        # Validate required fields
        if not body.mentor_id:
            raise HTTPException(status_code=400, detail="mentor_id is required")
        if not body.user_id:
            raise HTTPException(status_code=400, detail="user_id is required")

        # Get session date and time from either field
        session_date = body.session_date or body.date
        session_time = body.session_time or body.time

        if not session_date:
            raise HTTPException(status_code=400, detail="session_date is required")
        if not session_time:
            raise HTTPException(status_code=400, detail="session_time is required")

        result = service.book_session(
            user_id=body.user_id,
            mentor_id=body.mentor_id,
            session_date=session_date,
            session_time=session_time,
            duration_hours=body.duration_hours,
            topic=body.topic or body.message,
            notes=body.notes,
        )

        # Ensure result is serializable
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        # Convert datetime objects to strings for JSON serialization
        if "created_at" in result and hasattr(result["created_at"], "isoformat"):
            result["created_at"] = result["created_at"].isoformat()

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Booking error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mentors/sessions/{user_id}")
async def get_user_sessions(user_id: str):
    """Get user's mentoring sessions."""
    try:
        from backend.services.mentor_service import get_mentor_service
        service = get_mentor_service()

        sessions = service.get_user_sessions(user_id)
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Sessions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# WEBSOCKET ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.websocket("/ws/room/{room_id}/{role}")
async def websocket_room(websocket: WebSocket, room_id: str, role: str):
    """WebSocket endpoint for mentor matching rooms."""
    from backend.services.live_session import signaling

    if role not in ("mentor", "candidate"):
        await websocket.close(code=1008, reason="Invalid role")
        return

    await websocket.accept()
    await signaling.join_room(room_id, role, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            msg_type = message.get("type")

            if msg_type in ("offer", "answer", "ice-candidate", "chat"):
                await signaling.relay(room_id, role, {**message, "from": role})
            elif msg_type == "leave":
                break
    except WebSocketDisconnect:
        pass
    finally:
        await signaling.leave(room_id, role)


@app.websocket("/ws/interview/{session_id}")
async def websocket_interview_session(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for interview sessions (backward compatibility)."""
    from backend.services.live_session import signaling

    await websocket.accept()
    role = websocket.query_params.get("role", "candidate")

    if role not in ("mentor", "candidate"):
        await websocket.close(code=1008, reason="Invalid role")
        return

    await signaling.join_room(session_id, role, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")

            if msg_type in ("offer", "answer", "ice-candidate", "chat"):
                await signaling.relay(session_id, role, {**message, "from": role})
            elif msg_type == "leave":
                break
    except WebSocketDisconnect:
        pass
    finally:
        await signaling.leave(session_id, role)


# ─────────────────────────────────────────────────────────────────────────────
# TN AUTOMOTIVE TAXONOMY ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/tn-automotive/roles")
async def tn_automotive_roles():
    """List available TN automotive job roles."""
    try:
        from backend.services.tn_automotive_taxonomy import tn_extractor
        roles = tn_extractor.list_roles()
        return {"roles": roles}
    except Exception as e:
        logger.error(f"Roles error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tn-automotive/extract-skills")
async def tn_automotive_extract_skills(text: str):
    """Extract TN automotive skills from text."""
    try:
        from backend.services.tn_automotive_taxonomy import tn_extractor
        skills = tn_extractor.extract_skills(text)
        return {"skills": skills}
    except Exception as e:
        logger.error(f"Extract error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tn-automotive/gap-analysis")
async def tn_automotive_gap_analysis(text: str, role_name: str):
    """Analyze skill gaps for a TN automotive role."""
    try:
        from backend.services.tn_automotive_taxonomy import tn_extractor
        skills = tn_extractor.extract_skills(text)
        analysis = tn_extractor.get_skill_gaps_for_role(skills, role_name)
        return analysis
    except Exception as e:
        logger.error(f"Gap analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# SESSION MANAGEMENT ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/session/init")
async def init_session():
    """Initialize a new user session."""
    session_id = str(uuid.uuid4())
    return {"session_id": session_id}


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session state."""
    try:
        from backend.services.state_manager import state
        snapshot = state.snapshot(session_id)
        return snapshot
    except Exception as e:
        logger.error(f"Session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post( "/admin/reset-vector-store" )
async def admin_reset_vector_store () :
    """
    Reset vector store to fix dimension mismatch.
    Call this ONCE after switching embedding models.
    """
    try :
        import shutil
        from backend.config import settings
        from pathlib import Path

        chroma_dir = Path( settings.CHROMA_PERSIST_DIR )
        if chroma_dir.exists() :
            shutil.rmtree( chroma_dir )
            logger.info( f"Deleted {chroma_dir}" )
            chroma_dir.mkdir( parents=True, exist_ok=True )

        # Reinitialize vector store
        from backend.services.vector_store import vector_store
        from backend.services.vector_store import VectorStore

        # Force reinitialization
        vector_store.clear()

        return {
            "status" : "success",
            "message" : "Vector store reset. The next match request will re-index jobs.",
            "directory" : str( chroma_dir )
        }
    except Exception as e :
        logger.error( f"Reset error: {e}" )
        raise HTTPException( status_code=500, detail=str( e ) )


@app.post( "/admin/refresh-jobs" )
async def admin_refresh_jobs ( resume_text: str = "", location: str = "India" ) :
    """
    Manually refresh jobs in vector store.
    """
    try :
        from backend.services.job_scraper import get_job_scraper
        from backend.services.vector_store import vector_store
        from backend.services.matcher import get_job_matcher

        # Extract target role from resume or use default
        if resume_text :
            matcher = get_job_matcher()
            target_role = matcher._extract_target_role( resume_text )
        else :
            target_role = "Software Engineer"

        scraper = get_job_scraper()
        jobs = scraper.fetch_jobs( query=target_role, location=location, num_jobs=50 )

        if jobs :
            indexed = vector_store.index_jobs( jobs )
            return {
                "status" : "success",
                "jobs_fetched" : len( jobs ),
                "jobs_indexed" : indexed,
                "target_role" : target_role,
                "total_jobs" : vector_store.get_stats()["total_jobs"]
            }
        else :
            return {"status" : "error", "message" : "No jobs found"}
    except Exception as e :
        logger.error( f"Refresh jobs error: {e}" )
        raise HTTPException( status_code=500, detail=str( e ) )


# ─────────────────────────────────────────────────────────────────────────────
# VECTOR STORE MANAGEMENT ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.get( "/vector-store/status" )
async def vector_store_status () :
    """Check vector store status and contents."""
    try :
        from backend.services.vector_store import vector_store
        stats = vector_store.get_stats()

        # Get a sample of jobs
        sample = []
        if stats["total_jobs"] > 0 :
            try :
                sample_jobs = vector_store.search( "software", top_k=3 )
                sample = [
                    {
                        "title" : j.get( "title", "" ),
                        "company" : j.get( "company", "" ),
                        "location" : j.get( "location", "" )
                    }
                    for j in sample_jobs
                ]
            except Exception as e :
                sample = [{"error" : str( e )}]

        return {
            "total_jobs" : stats["total_jobs"],
            "freshness" : stats.get( "freshness", "unknown" ),
            "embedder" : stats.get( "embedder", "unknown" ),
            "sample_jobs" : sample,
            "collection_exists" : True
        }
    except Exception as e :
        logger.error( f"Status error: {e}" )
        return {"error" : str( e ), "total_jobs" : 0}


@app.post( "/admin/reset-vector-store" )
async def admin_reset_vector_store () :
    """
    Reset vector store to fix dimension mismatch.
    Call this ONCE after switching embedding models.
    """
    try :
        import shutil
        from backend.config import settings
        from pathlib import Path

        chroma_dir = Path( settings.CHROMA_PERSIST_DIR )
        if chroma_dir.exists() :
            shutil.rmtree( chroma_dir )
            logger.info( f"Deleted {chroma_dir}" )
            chroma_dir.mkdir( parents=True, exist_ok=True )

        # Reinitialize vector store
        from backend.services.vector_store import vector_store
        vector_store.clear()

        return {
            "status" : "success",
            "message" : "Vector store reset. The next match request will re-index jobs.",
            "directory" : str( chroma_dir )
        }
    except Exception as e :
        logger.error( f"Reset error: {e}" )
        raise HTTPException( status_code=500, detail=str( e ) )


@app.post( "/admin/force-refresh-jobs" )
async def admin_force_refresh_jobs (
        query: str = "Software Engineer",
        location: str = "India",
        num_jobs: int = 30
) :
    """Force refresh jobs - clear and re-index."""
    try :
        from backend.services.job_scraper import get_job_scraper
        from backend.services.vector_store import vector_store

        logger.info( f"Force refreshing jobs for query: {query}, location: {location}" )

        # Clear existing jobs
        vector_store.clear()
        logger.info( "Cleared existing jobs" )

        # Fetch fresh jobs
        scraper = get_job_scraper()
        jobs = scraper.fetch_jobs(
            query=query,
            location=location,
            num_jobs=num_jobs,
            days_old=30
        )

        logger.info( f"Fetched {len( jobs )} jobs from scraper" )

        if not jobs :
            return {
                "status" : "error",
                "message" : f"No jobs found for query '{query}' in {location}",
                "jobs_fetched" : 0
            }

        # Index jobs
        indexed = vector_store.index_jobs( jobs )

        # Verify indexing worked
        final_stats = vector_store.get_stats()

        return {
            "status" : "success",
            "query" : query,
            "location" : location,
            "jobs_fetched" : len( jobs ),
            "jobs_indexed" : indexed,
            "total_jobs_in_store" : final_stats["total_jobs"],
            "sample_job" : jobs[0] if jobs else None
        }

    except Exception as e :
        logger.error( f"Force refresh error: {e}", exc_info=True )
        raise HTTPException( status_code=500, detail=str( e ) )


@app.post( "/admin/seed-mock-jobs" )
async def admin_seed_mock_jobs ( query: str = "Software Engineer", location: str = "India", num_jobs: int = 20 ) :
    """Seed vector store with mock jobs for testing."""
    try :
        from backend.services.vector_store import vector_store

        # Clear existing
        vector_store.clear()

        # Generate mock jobs directly
        mock_jobs = []
        roles = [
            f"Senior {query}", f"Junior {query}", f"Lead {query}",
            f"{query} Specialist", f"{query} Developer", f"Principal {query}",
            f"{query} Architect", f"{query} Consultant", f"Staff {query}"
        ]
        companies = ["Google", "Microsoft", "Amazon", "Apple", "Meta", "Netflix", "Tesla"]

        for i in range( num_jobs ) :
            job_id = f"seed_job_{i}"
            mock_jobs.append( {
                "id" : job_id,
                "title" : roles[i % len( roles )],
                "company" : companies[i % len( companies )],
                "location" : location,
                "description" : f"We are hiring a {roles[i % len( roles )]} at {companies[i % len( companies )]}. "
                                f"Requirements: Experience in {query}, strong coding skills, team player.",
                "apply_link" : f"https://example.com/jobs/{job_id}",
                "posted_at" : f"{i + 1} days ago",
                "employment_type" : "Full-time",
                "days_old" : i,
                "fetched_at" : datetime.now().isoformat(),
            } )

        indexed = vector_store.index_jobs( mock_jobs )

        return {
            "status" : "success",
            "jobs_created" : len( mock_jobs ),
            "jobs_indexed" : indexed,
            "total_jobs" : vector_store.get_stats()["total_jobs"]
        }
    except Exception as e :
        logger.error( f"Seed error: {e}" )
        raise HTTPException( status_code=500, detail=str( e ) )
# ─────────────────────────────────────────────────────────────────────────────
# INTERVIEW — LIVE REST ENDPOINTS  (/interview/live/start, /interview/live/next)
# ─────────────────────────────────────────────────────────────────────────────

class LiveInterviewStartRequest(BaseModel):
    role: str
    interview_type: str = "mixed"
    resume_text: str = ""
    num_questions: int = 10


class LiveInterviewNextRequest(BaseModel):
    session_id: str
    transcript: str


@app.post("/interview/live/start")
async def live_interview_start(request: LiveInterviewStartRequest):
    """Start a live AI mock-interview session and return the first question."""
    try:
        from backend.services.live_session import interview_engine
        session_id = str(__import__("uuid").uuid4())
        result = interview_engine.start_session(
            session_id=session_id,
            role=request.role,
            interview_type=request.interview_type,
            resume_text=request.resume_text,
            num_questions=request.num_questions,
        )
        return result
    except Exception as e:
        logger.error(f"Live interview start error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/interview/live/next")
async def live_interview_next(request: LiveInterviewNextRequest):
    """Submit answer transcript and get the next question (or final summary)."""
    try:
        from backend.services.live_session import interview_engine
        result = interview_engine.next_question(
            session_id=request.session_id,
            transcript=request.transcript,
        )
        return result
    except Exception as e:
        logger.error(f"Live interview next error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# HR PANEL GENERATOR  (self-contained — produces the exact shape HRResults needs)
# ─────────────────────────────────────────────────────────────────────────────

def _generate_hr_panel(
    resume_text: str,
    target_role: str,
    company_type: Optional[str] = None,
    focus_area: Optional[str] = None,
    num_questions: int = 8,
) -> Dict:
    """
    Call the LLM to produce a full HR recruiter panel in the exact JSON shape
    that the frontend HRResults component expects:
      hire_verdict, verdict_summary, verdict_confidence,
      dimension_scores, green_flags, red_flags,
      questions_to_ask, salary_bracket_inr,
      suggested_interview_rounds, recruiter_notes
    """
    import re as _re
    from backend.services.llm import llm_call_sync

    company_ctx = company_type or "mid-size"
    focus_ctx   = focus_area   or "general"

    prompt = f"""You are a senior HR recruiter at a {company_ctx} tech company doing a {focus_ctx} evaluation.
Analyse the resume below for the role of "{target_role}" and return ONLY a single valid JSON object.

CRITICAL JSON RULES:
- Double quotes for ALL strings
- No trailing commas
- Escape any double quotes inside string values with backslash
- All text on single lines (no newlines inside string values)

RESUME:
{resume_text[:4000]}

Return EXACTLY this structure (fill in real values — do NOT keep placeholders):
{{
  "hire_verdict": "Yes",
  "verdict_summary": "one sentence summary of hiring decision",
  "verdict_confidence": 72,
  "dimension_scores": {{
    "technical_fit": 7,
    "experience_relevance": 6,
    "culture_fit": 7,
    "growth_potential": 8,
    "communication_clarity": 7
  }},
  "green_flags": ["strength 1", "strength 2", "strength 3"],
  "red_flags": ["concern 1", "concern 2"],
  "questions_to_ask": [
    {{"question": "Tell me about a challenging project.", "type": "behavioural", "reason": "Assesses problem-solving."}},
    {{"question": "How do you stay current with {target_role} trends?", "type": "technical", "reason": "Checks continuous learning."}}
  ],
  "salary_bracket_inr": "12-18 LPA",
  "suggested_interview_rounds": ["HR Screening", "Technical Round", "Manager Round"],
  "recruiter_notes": "Internal candid note about this candidate."
}}

hire_verdict must be one of: "Strong Yes", "Yes", "Maybe", "No", "Strong No"
questions_to_ask must have exactly {num_questions} items, type must be one of: technical, behavioural, situational
"""

    try:
        raw = llm_call_sync(
            system="You are an expert HR recruiter AI. Respond with ONLY valid JSON. No markdown, no extra text.",
            user=prompt,
            temp=0.3,
            max_tokens=2000,
        )
    except Exception as e:
        logger.error(f"HR panel LLM call failed: {e}")
        return _hr_panel_fallback(target_role, company_type)

    # ── Clean response ────────────────────────────────────────────────────────
    raw = _re.sub(r'```json\s*', '', raw or '')
    raw = _re.sub(r'```\s*', '', raw)
    start = raw.find('{')
    end   = raw.rfind('}')
    if start >= 0 and end > start:
        raw = raw[start:end + 1]
    else:
        return _hr_panel_fallback(target_role, company_type)

    raw = _re.sub(r',\s*}', '}', raw)
    raw = _re.sub(r',\s*]', ']', raw)

    # ── Parse ─────────────────────────────────────────────────────────────────
    result = None
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        # Try closing unclosed braces
        try:
            raw += '}' * (raw.count('{') - raw.count('}'))
            result = json.loads(raw)
        except Exception:
            pass

    if not isinstance(result, dict):
        return _hr_panel_fallback(target_role, company_type)

    # ── Validate & fill defaults ──────────────────────────────────────────────
    valid_verdicts = {"Strong Yes", "Yes", "Maybe", "No", "Strong No"}
    if result.get("hire_verdict") not in valid_verdicts:
        result["hire_verdict"] = "Maybe"

    result.setdefault("verdict_summary",   "Resume reviewed by AI recruiter.")
    result.setdefault("verdict_confidence", 60)
    result.setdefault("dimension_scores", {
        "technical_fit": 5, "experience_relevance": 5,
        "culture_fit": 5, "growth_potential": 5, "communication_clarity": 5,
    })
    result.setdefault("green_flags",   [])
    result.setdefault("red_flags",     [])
    result.setdefault("questions_to_ask", [])
    result.setdefault("salary_bracket_inr",          "Market rate")
    result.setdefault("suggested_interview_rounds",  ["HR Screening", "Technical Round"])
    result.setdefault("recruiter_notes",             "Candidate requires further evaluation.")

    # Clamp confidence
    try:
        result["verdict_confidence"] = max(0, min(100, int(result["verdict_confidence"])))
    except (ValueError, TypeError):
        result["verdict_confidence"] = 60

    # Clamp dimension scores to 0–10
    for k, v in result.get("dimension_scores", {}).items():
        try:
            result["dimension_scores"][k] = max(0, min(10, int(v)))
        except (ValueError, TypeError):
            result["dimension_scores"][k] = 5

    # Ensure questions have required keys
    cleaned_questions = []
    valid_types = {"technical", "behavioural", "situational"}
    for q in result.get("questions_to_ask", []):
        if isinstance(q, dict) and q.get("question"):
            cleaned_questions.append({
                "question": str(q.get("question", "")),
                "type":     q.get("type", "behavioural") if q.get("type") in valid_types else "behavioural",
                "reason":   str(q.get("reason", "")),
            })
    result["questions_to_ask"] = cleaned_questions

    return result


def _hr_panel_fallback(target_role: str, company_type: Optional[str]) -> Dict:
    """Fallback HR panel when LLM call or parsing fails."""
    return {
        "hire_verdict":            "Maybe",
        "verdict_summary":         f"Could not fully evaluate candidate for {target_role}. Manual review recommended.",
        "verdict_confidence":      50,
        "dimension_scores": {
            "technical_fit":         5,
            "experience_relevance":  5,
            "culture_fit":           5,
            "growth_potential":      5,
            "communication_clarity": 5,
        },
        "green_flags":  ["Resume submitted for review"],
        "red_flags":    ["Automated analysis incomplete — please review manually"],
        "questions_to_ask": [
            {"question": f"Walk me through your most relevant experience for this {target_role} role.", "type": "behavioural", "reason": "Establishes baseline fit."},
            {"question": "What motivated you to apply for this position?",                              "type": "behavioural", "reason": "Gauges genuine interest."},
            {"question": "Describe a challenging problem you solved recently.",                         "type": "situational", "reason": "Assesses problem-solving ability."},
        ],
        "salary_bracket_inr":         "Market rate",
        "suggested_interview_rounds":  ["HR Screening", "Technical Round", "Manager Round"],
        "recruiter_notes":             "Automated HR panel generation encountered an error. Manual screening advised.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# RESUME ANALYZER  (/resume/analyze)  +  HR PANEL  (/interview/hr-panel)
# ─────────────────────────────────────────────────────────────────────────────

class ResumeAnalyzeRequest(BaseModel):
    resume_text: str
    target_role: str = "Software Engineer"
    job_description: Optional[str] = None
    company_type: Optional[str] = None
    focus_area: Optional[str] = None


@app.post("/resume/analyze")
async def analyze_resume(request: ResumeAnalyzeRequest):
    """ATS score + HR panel in one call (used by ResumeAnalyzer component)."""
    ats_result = None
    ats_error  = None
    hr_panel   = None
    hr_error   = None

    # ── ATS scoring ──────────────────────────────────────────────────────────
    try:
        from backend.services.ats_scorer import get_ats_scorer
        scorer = get_ats_scorer()
        ats_result = scorer.score(
            resume_text=request.resume_text,
            target_role=request.target_role,
            job_description=request.job_description or "",
        )
    except Exception as e:
        ats_error = str(e)
        logger.error(f"ATS scoring error: {e}", exc_info=True)

    # ── HR panel ─────────────────────────────────────────────────────────────
    try:
        hr_panel = _generate_hr_panel(
            resume_text=request.resume_text,
            target_role=request.target_role,
            company_type=request.company_type,
            focus_area=request.focus_area,
            num_questions=8,
        )
    except Exception as e:
        hr_error = str(e)
        logger.error(f"HR panel generation error: {e}", exc_info=True)

    return {
        "ats_result": ats_result,
        "ats_error":  ats_error,
        "hr_panel":   hr_panel,
        "hr_error":   hr_error,
    }


class HRPanelRequest(BaseModel):
    resume_text: str
    target_role: str = "Software Engineer"
    company_type: Optional[str] = None
    focus_area: Optional[str] = None


@app.post("/interview/hr-panel")
async def hr_panel_endpoint(request: HRPanelRequest):
    """Generate a full HR recruiter panel for a resume + target role."""
    try:
        panel = _generate_hr_panel(
            resume_text=request.resume_text,
            target_role=request.target_role,
            company_type=request.company_type,
            focus_area=request.focus_area,
            num_questions=10,
        )
        return {"panel": panel}
    except Exception as e:
        logger.error(f"HR panel error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# TN ANALYTICS  (/tn/batch-analytics)
# ─────────────────────────────────────────────────────────────────────────────

class TNBatchAnalyticsRequest(BaseModel):
    institution_name: Optional[str] = None
    profiles: List[Dict]


@app.post("/tn/batch-analytics")
async def tn_batch_analytics(request: TNBatchAnalyticsRequest):
    """Run batch skill analytics on a list of student/worker profiles."""
    try:
        from backend.services.tn_automotive_taxonomy import TNAutomotiveSkillExtractor
        taxonomy = TNAutomotiveSkillExtractor()
        result = taxonomy.batch_analyze(request.profiles)
        if request.institution_name:
            result["institution_name"] = request.institution_name
        return result
    except Exception as e:
        logger.error(f"TN batch analytics error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# RANKING / LTR PREFERENCE  (/ranking/preference)
# ─────────────────────────────────────────────────────────────────────────────

class RankingPreferenceBody(BaseModel):
    user_id: str
    winner: Dict
    loser: Dict
    context: Optional[Dict] = None


@app.post("/ranking/preference")
async def record_ranking_preference(body: RankingPreferenceBody):
    """Record a pairwise preference signal for the Learning-to-Rank model."""
    try:
        from backend.services.learning_to_rank import get_ltr_engine
        engine = get_ltr_engine()
        result = engine.record_preference(
            user_id=body.user_id,
            winner=body.winner,
            loser=body.loser,
            context=body.context,
        )
        return result
    except Exception as e:
        logger.error(f"Ranking preference error: {e}", exc_info=True)
        # Non-critical — return 200 so the UI doesn't surface an error
        return {"status": "skipped", "reason": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# MENTOR DOMAINS  (/mentor/domains)
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/mentor/domains")
async def mentor_domains():
    """Return the list of available mentor expertise domains."""
    try:
        from backend.services.mentor_service import get_mentor_service
        svc = get_mentor_service()
        if hasattr(svc, "get_domains"):
            return {"domains": svc.get_domains()}
        # Fallback: derive from mentor data
        mentors = svc.search_mentors()
        domains = sorted({d for m in mentors for d in (m.get("expertise") or [])})
        return {"domains": domains}
    except Exception as e:
        logger.error(f"Mentor domains error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )