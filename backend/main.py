from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import tempfile
import os
import logging
from pathlib import Path

from backend.config import settings
from backend.models import (
    ResumeUploadResponse, JobMatchRequest, JobMatchResponse,
    ConfigResponse, JobMatch,
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
from backend.models import (
    DSAProblem, DSAProgressUpdate, DSABulkUpdate,
    RoadmapCheckpointUpdate,
    ProjectStatus, ProjectStatusUpdate,
    InterviewEntryCreate, InterviewRoundAdd, InterviewOutcomeUpdate,
    InterviewRound,
)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Career Genie – TN AUTO SkillBridge",
    description="AI-powered workforce analytics · Job Coach · Market Insights · Interview Coach",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)


# ============================================================================
# REQUEST MODELS
# ============================================================================

class RoadmapRequest(BaseModel):
    resume_text: str
    target_role: str
    skill_gaps: List[str] = []
    duration_weeks: int = 12
    experience_level: Optional[str] = None


class ProjectRequest(BaseModel):
    resume_text: str
    target_role: str
    skill_gaps: List[str] = []
    difficulty: Optional[str] = "intermediate"
    num_projects: int = 5


class TNSkillAnalysisRequest(BaseModel):
    profile_text: str
    target_role: Optional[str] = None


class BatchProfileItem(BaseModel):
    id: str
    name: str
    text: str
    target_role: Optional[str] = None


class BatchAnalysisRequest(BaseModel):
    institution_name: Optional[str] = "Tamil Nadu ITI / Polytechnic"
    profiles: List[BatchProfileItem]


# ── New feature request models ───────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str   # "user" or "assistant"
    content: str


class JobCoachRequest(BaseModel):
    messages: List[ChatMessage]
    resume_text: Optional[str] = None


class MarketInsightsRequest(BaseModel):
    role: str
    skills: Optional[List[str]] = None
    location: str = "India"


class InterviewChatRequest(BaseModel):
    messages: List[ChatMessage]
    role: str
    interview_type: str = "mixed"   # "technical" | "behavioural" | "hr" | "mixed"
    resume_text: Optional[str] = None


class InterviewQuestionsRequest(BaseModel):
    role: str
    interview_type: str = "mixed"
    resume_text: Optional[str] = None
    num_questions: int = 10


class EvaluateAnswerRequest(BaseModel):
    question: str
    answer: str
    role: str
    interview_type: str = "mixed"


# ============================================================================
# CONFIG
# ============================================================================

@app.get("/config", response_model=ConfigResponse)
def get_config():
    return ConfigResponse(
        serpapi_key_present=bool(settings.SERPAPI_KEY),
        searchapi_key_present=bool(settings.SERPAPI_KEY),
        anthropic_key_present=bool(settings.GROQ_API_KEY),   # reuse field for Groq
        vector_db_initialized=True,
        total_indexed_jobs=vector_store.collection.count()
    )


# ============================================================================
# RESUME UPLOAD
# ============================================================================

@app.post("/upload-resume/parse", response_model=ResumeUploadResponse)
async def parse_resume(file: UploadFile = File(...)):
    logger.info(f"Resume upload: {file.filename}")
    if not file.filename.lower().endswith(('.pdf', '.docx', '.doc')):
        raise HTTPException(status_code=400, detail="Invalid format. Upload PDF or DOCX.")
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        temp_path = tmp.name
    try:
        result = resume_parser.parse(temp_path)
        return ResumeUploadResponse(status="success", resume_text=result['resume_text'],
                                    word_count=result['word_count'])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {e}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


# ============================================================================
# JOB MATCHING
# ============================================================================

@app.post("/rag/match-realtime", response_model=JobMatchResponse)
def match_jobs_realtime(request: JobMatchRequest):
    if not request.resume_text.strip():
        raise HTTPException(status_code=400, detail="Resume text is required")
    if not request.job_query.strip():
        raise HTTPException(status_code=400, detail="Job query is required")
    try:
        jobs = get_job_scraper().fetch_jobs(query=request.job_query, location=request.location,
                                            num_jobs=request.num_jobs)
        if not jobs:
            return JobMatchResponse(matched_jobs=[], total_jobs_fetched=0, total_jobs_indexed=0,
                                    search_query=f"{request.job_query} in {request.location}")
        try:
            from backend.services.job_filter import SmartJobFilter
            filtered = SmartJobFilter().filter_jobs(
                jobs, min_match_score=request.min_match_score,
                experience_level=request.experience_level,
                posted_within_days=request.posted_within_days,
                exclude_remote=request.exclude_remote)
            jobs_to_index = filtered if filtered else jobs
        except ImportError:
            jobs_to_index = jobs

        indexed_count = vector_store.index_jobs(jobs_to_index)
        if indexed_count == 0:
            raise HTTPException(status_code=500, detail="Failed to index jobs")

        matches = get_job_matcher().match_resume_to_jobs(resume_text=request.resume_text, top_k=request.top_k)

        career_advice_data = None
        if career_advisor:
            try:
                career_advice_data = career_advisor.generate_career_advice(
                    resume_text=request.resume_text, target_role=request.job_query,
                    current_role=None, job_matches=matches[:3])
            except Exception as e:
                logger.error(f"Career advice failed: {e}")

        skill_comparison_data = None
        try:
            if matches:
                rs = get_job_matcher()._extract_skills(request.resume_text)
                js = get_job_matcher()._extract_skills(matches[0].get('description', ''))
                skill_comparison_data = {
                    "overall_match": matches[0].get('match_score', 0),
                    "matched_skills": [{"skill": s, "status": "qualified"} for s in set(rs) & set(js)],
                    "skill_gaps": [{"skill": s, "resume_level": "none", "required_level": "intermediate",
                                    "gap_severity": "moderate"} for s in set(js) - set(rs)],
                    "bonus_skills": [{"skill": s} for s in set(rs) - set(js)],
                    "resume_skills": [{"skill": s, "category": "Programming"} for s in rs],
                    "job_skills": [{"skill": s, "category": "Programming"} for s in js],
                }
        except Exception as e:
            logger.error(f"Skill comparison failed: {e}")

        resp = {"matched_jobs": [JobMatch(**m) for m in matches],
                "total_jobs_fetched": len(jobs), "total_jobs_indexed": indexed_count,
                "search_query": f"{request.job_query} in {request.location}"}
        if career_advice_data:
            resp["career_advice"] = career_advice_data
        if skill_comparison_data:
            resp["skill_comparison"] = skill_comparison_data
        return JobMatchResponse(**resp)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Job matching error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Job matching failed: {e}")


# ============================================================================
# ROADMAP & PROJECTS
# ============================================================================

@app.post("/generate/roadmap")
def generate_roadmap(request: RoadmapRequest):
    if not request.target_role.strip():
        raise HTTPException(status_code=400, detail="target_role is required")
    try:
        roadmap = get_roadmap_generator().generate_roadmap(
            resume_text=request.resume_text, target_role=request.target_role,
            skill_gaps=request.skill_gaps, duration_weeks=request.duration_weeks,
            experience_level=request.experience_level)
        return {"status": "success", "roadmap": roadmap}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate/projects")
def generate_projects(request: ProjectRequest):
    if not request.target_role.strip():
        raise HTTPException(status_code=400, detail="target_role is required")
    try:
        projects = get_project_generator().suggest_projects(
            resume_text=request.resume_text, target_role=request.target_role,
            skill_gaps=request.skill_gaps, difficulty=request.difficulty,
            num_projects=request.num_projects)
        return {"status": "success", "projects": projects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ROUTE ALIASES  (frontend calls /roadmap/generate and /projects/suggest)
# ============================================================================

@app.post("/roadmap/generate")
def generate_roadmap_alias(request: RoadmapRequest):
    """Alias for /generate/roadmap — keeps frontend URLs working."""
    return generate_roadmap(request)


@app.post("/projects/suggest")
def suggest_projects_alias(request: ProjectRequest):
    """Alias for /generate/projects — keeps frontend URLs working."""
    return generate_projects(request)


# ============================================================================
# JOB COACH CHATBOT  ← NEW
# ============================================================================

@app.post("/coach/chat")
def job_coach_chat(request: JobCoachRequest):
    """
    Conversational job coach / career counsellor.
    Send a conversation history and get the coach's next response.
    Optionally include resume_text for personalised advice.
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages list is required")
    try:
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        reply = get_job_coach().chat(messages=messages, resume_text=request.resume_text)
        return {"status": "success", "reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MARKET INSIGHTS  ← NEW
# ============================================================================

@app.post("/insights/market")
def market_insights(request: MarketInsightsRequest):
    """
    Fetch Google Trends data for a role + skills and generate an AI
    market analysis report.
    """
    if not request.role.strip():
        raise HTTPException(status_code=400, detail="role is required")
    try:
        result = get_market_insights().get_insights(
            role=request.role, skills=request.skills, location=request.location)
        return {"status": "success", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# INTERVIEW COACH  ← NEW
# ============================================================================

@app.post("/interview/questions")
def get_interview_questions(request: InterviewQuestionsRequest):
    """Generate a bank of interview questions for a role."""
    if not request.role.strip():
        raise HTTPException(status_code=400, detail="role is required")
    try:
        questions = get_interview_coach().generate_questions(
            role=request.role, interview_type=request.interview_type,
            resume_text=request.resume_text, num_questions=request.num_questions)
        return {"status": "success", "questions": questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/interview/chat")
def interview_chat(request: InterviewChatRequest):
    """
    Live mock interview via back-and-forth chat.
    The AI acts as the interviewer, asks questions, and evaluates answers.
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages list is required")
    if not request.role.strip():
        raise HTTPException(status_code=400, detail="role is required")
    try:
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        reply = get_interview_coach().chat(
            messages=messages, role=request.role,
            interview_type=request.interview_type, resume_text=request.resume_text)
        return {"status": "success", "reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/interview/evaluate")
def evaluate_answer(request: EvaluateAnswerRequest):
    """
    Evaluate a candidate's answer to an interview question.
    Returns score, strengths, improvements, and a model answer.
    """
    if not request.question.strip() or not request.answer.strip():
        raise HTTPException(status_code=400, detail="question and answer are required")
    try:
        feedback = get_interview_coach().evaluate_answer(
            question=request.question, answer=request.answer,
            role=request.role, interview_type=request.interview_type)
        return {"status": "success", "feedback": feedback}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROGRESS TRACKING — DSA
# ============================================================================

@app.get("/progress/dsa")
def list_dsa_problems(topic: Optional[str] = None, difficulty: Optional[str] = None,
                       solved: Optional[bool] = None):
    """List all DSA problems with optional filters."""
    problems = progress_store.get_all_dsa()
    if topic:
        problems = [p for p in problems if p.get("topic") == topic]
    if difficulty:
        problems = [p for p in problems if p.get("difficulty") == difficulty]
    if solved is not None:
        problems = [p for p in problems if p.get("solved") == solved]
    return {"status": "success", "problems": problems, "count": len(problems)}


@app.post("/progress/dsa/add")
def add_dsa_problem(problem: DSAProblem):
    """Add a custom DSA problem."""
    saved = progress_store.upsert_dsa_problem(problem.dict())
    return {"status": "success", "problem": saved}


@app.patch("/progress/dsa/update")
def update_dsa_problem(update: DSAProgressUpdate):
    """Mark a DSA problem as solved/unsolved."""
    result = progress_store.update_dsa_progress(
        update.problem_id, update.solved, update.attempts, update.notes)
    if not result:
        raise HTTPException(status_code=404, detail="Problem not found")
    return {"status": "success", "problem": result}


@app.patch("/progress/dsa/bulk-update")
def bulk_update_dsa(bulk: DSABulkUpdate):
    """Bulk update multiple DSA problems."""
    results = []
    for u in bulk.updates:
        r = progress_store.update_dsa_progress(u.problem_id, u.solved, u.attempts, u.notes)
        if r:
            results.append(r)
    return {"status": "success", "updated": len(results), "problems": results}


# ============================================================================
# PROGRESS TRACKING — ROADMAP
# ============================================================================

@app.get("/progress/roadmap/{roadmap_id}")
def get_roadmap_progress(roadmap_id: str):
    """Get all completed checkpoints for a roadmap."""
    checkpoints = progress_store.get_roadmap_progress(roadmap_id)
    return {"status": "success", "roadmap_id": roadmap_id,
            "checkpoints": checkpoints, "count": len(checkpoints)}


@app.post("/progress/roadmap/checkpoint")
def update_roadmap_checkpoint(update: RoadmapCheckpointUpdate):
    """Mark a roadmap week/phase checkpoint as done."""
    result = progress_store.update_roadmap_checkpoint(
        update.roadmap_id, update.phase_number, update.week_number,
        update.completed, update.hours_logged or 0.0, update.notes or "")
    return {"status": "success", "checkpoint": result}


# ============================================================================
# PROGRESS TRACKING — PROJECTS
# ============================================================================

@app.get("/progress/projects")
def list_projects():
    """Get all project statuses."""
    return {"status": "success", "projects": progress_store.get_all_projects()}


@app.post("/progress/projects")
def add_project(project: ProjectStatus):
    """Add or upsert a project status."""
    saved = progress_store.upsert_project(project.dict())
    return {"status": "success", "project": saved}


@app.patch("/progress/projects/update")
def update_project(update: ProjectStatusUpdate):
    """Update project status, progress, or add a milestone."""
    result = progress_store.update_project(
        update.project_id,
        status=update.status,
        github_url=update.github_url,
        live_url=update.live_url,
        progress_percent=update.progress_percent,
        milestone_done=update.milestone_done,
        notes=update.notes,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "success", "project": result}


# ============================================================================
# PROGRESS TRACKING — INTERVIEW TRACKER
# ============================================================================

@app.get("/progress/interviews")
def list_interviews():
    """Get all interview entries."""
    return {"status": "success", "interviews": progress_store.get_all_interviews()}


@app.post("/progress/interviews")
def create_interview(req: InterviewEntryCreate):
    """Create a new interview/application entry."""
    entry = progress_store.create_interview(
        req.company, req.role, req.job_url or "", req.applied_at or "")
    return {"status": "success", "interview": entry}


@app.post("/progress/interviews/round")
def add_interview_round(req: InterviewRoundAdd):
    """Add a new round to an existing interview entry."""
    result = progress_store.add_interview_round(req.interview_id, req.round.dict())
    if not result:
        raise HTTPException(status_code=404, detail="Interview entry not found")
    return {"status": "success", "interview": result}


@app.patch("/progress/interviews/outcome")
def update_interview_outcome(req: InterviewOutcomeUpdate):
    """Update the final outcome of an interview (offer/rejected/withdrawn)."""
    result = progress_store.update_interview_outcome(
        req.interview_id, req.final_outcome,
        req.offer_details, req.notes or "")
    if not result:
        raise HTTPException(status_code=404, detail="Interview entry not found")
    return {"status": "success", "interview": result}


# ============================================================================
# ANALYTICS DASHBOARD
# ============================================================================

@app.get("/progress/summary")
def progress_summary():
    """Full analytics summary — feeds the dashboard."""
    return {"status": "success", **progress_store.get_summary()}


# ============================================================================
# USER-SCOPED PROGRESS ALIASES  (frontend calls /progress/{user_id}/...)
# The app is single-user; user_id is accepted but ignored.
# ============================================================================

@app.get("/progress/{user_id}/summary")
def progress_summary_by_user(user_id: str):
    """User-scoped alias for /progress/summary."""
    return {"status": "success", **progress_store.get_summary()}


@app.get("/progress/{user_id}")
def progress_overview_by_user(user_id: str):
    """User-scoped overview: summary + all DSA, projects, interviews."""
    summary = progress_store.get_summary()
    return {
        "status": "success",
        "user_id": user_id,
        "summary": summary,
        "dsa_problems": progress_store.get_all_dsa(),
        "projects": progress_store.get_all_projects(),
        "interviews": progress_store.get_all_interviews(),
    }


@app.get("/progress/{user_id}/interviews/analytics")
def interview_analytics_by_user(user_id: str):
    """User-scoped interview analytics."""
    interviews = progress_store.get_all_interviews()
    total = len(interviews)
    offers   = sum(1 for iv in interviews if iv.get("final_outcome") == "offer")
    rejected = sum(1 for iv in interviews if iv.get("final_outcome") == "rejected")
    active   = total - offers - rejected

    # Stage breakdown
    stage_counts: Dict[str, int] = {}
    for iv in interviews:
        stage = iv.get("current_stage", "Applied")
        stage_counts[stage] = stage_counts.get(stage, 0) + 1

    # Company list
    companies = [{"company": iv.get("company"), "role": iv.get("role"),
                  "stage": iv.get("current_stage"), "outcome": iv.get("final_outcome")}
                 for iv in interviews]

    return {
        "status": "success",
        "user_id": user_id,
        "analytics": {
            "total": total,
            "offers": offers,
            "rejected": rejected,
            "active": active,
            "offer_rate": round(offers / total * 100, 1) if total else 0,
            "stage_breakdown": stage_counts,
            "companies": companies,
        },
    }


# ============================================================================
# TN AUTOMOTIVE
# ============================================================================

@app.post("/tn/analyze-profile")
def analyze_tn_profile(request: TNSkillAnalysisRequest):
    extracted = tn_extractor.extract_skills(request.profile_text)
    result = {"extracted_skills": extracted, "total_skills_found": len(extracted),
               "nsqf_summary": _build_nsqf_summary(extracted), "role_analysis": None}
    if request.target_role:
        result["role_analysis"] = tn_extractor.get_skill_gaps_for_role(extracted, request.target_role)
    return result


@app.post("/tn/batch-analytics")
def batch_analytics(request: BatchAnalysisRequest):
    if not request.profiles:
        raise HTTPException(status_code=400, detail="No profiles provided")
    if len(request.profiles) > 500:
        raise HTTPException(status_code=400, detail="Maximum 500 profiles per batch")
    logger.info(f"Batch analytics: {len(request.profiles)} profiles — '{request.institution_name}'")
    analytics = tn_extractor.batch_analyze([p.dict() for p in request.profiles])
    return {"institution": request.institution_name, "status": "success", **analytics}


@app.get("/tn/roles")
def list_tn_roles():
    return {"roles": [
        {"role": name, "description": d["description"], "cluster": d["cluster"],
         "nsqf_target": d["nsqf_target"],
         "nsqf_target_label": NSQF_LEVELS[d["nsqf_target"]]["label"],
         "required_skills": d["required_skills"], "preferred_skills": d["preferred_skills"],
         "typical_employers": d["typical_employer"]}
        for name, d in tn_extractor.job_roles.items()
    ]}


@app.get("/tn/skills")
def list_tn_skills():
    return {"total_skills": len(TN_SKILL_DB), "skills": [
        {"skill": s["skill"], "category": s["category"], "sector": s["sector"],
         "nsqf_level": s["nsqf_level"], "nsqf_label": NSQF_LEVELS[s["nsqf_level"]]["label"],
         "training_sources": s["training_src"]}
        for s in TN_SKILL_DB
    ], "nsqf_levels": NSQF_LEVELS}


# ============================================================================
# STATS & HEALTH
# ============================================================================

@app.get("/rag/stats")
def get_stats():
    return vector_store.get_stats()


@app.get("/health")
def health_check():
    errors = settings.validate()
    return {
        "status": "healthy" if not errors else "degraded",
        "errors": errors,
        "vector_db_jobs": vector_store.collection.count(),
        "services": {
            "vector_store": "ok",
            "job_scraper": "ok" if settings.SERPAPI_KEY else "missing_api_key",
            "career_advisor": "ok" if career_advisor else "not_initialized",
            "groq_llm": "ok" if settings.GROQ_API_KEY else "missing_api_key",
            "job_coach": "ok" if settings.GROQ_API_KEY else "missing_api_key",
            "market_insights": "ok" if settings.GROQ_API_KEY else "missing_api_key",
            "interview_coach": "ok" if settings.GROQ_API_KEY else "missing_api_key",
            "tn_automotive_taxonomy": f"ok — {len(tn_extractor.skill_db)} skills",
        }
    }


# ============================================================================
# HELPERS
# ============================================================================

def _build_nsqf_summary(extracted_skills: List[Dict]) -> Dict:
    if not extracted_skills:
        return {"peak_level": 1, "peak_label": NSQF_LEVELS[1]["label"], "distribution": {}}
    dist: Dict[int, List] = {}
    for s in extracted_skills:
        dist.setdefault(s["nsqf_level"], []).append(s["skill"])
    peak = max(dist.keys())
    return {"peak_level": peak, "peak_label": NSQF_LEVELS[peak]["label"],
            "distribution": {NSQF_LEVELS[lvl]["label"]: skills for lvl, skills in sorted(dist.items())}}


# ============================================================================
# STARTUP
# ============================================================================

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("Career Genie – TN AUTO SkillBridge v3.0 (Groq-powered)")
    logger.info("=" * 60)
    Path(settings.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
    for err in settings.validate():
        logger.error(f"  ❌ {err}")
    if not settings.validate():
        logger.info("✅ All configurations valid")
    logger.info(f"✅ TN taxonomy: {len(tn_extractor.skill_db)} skills · {len(tn_extractor.job_roles)} roles")
    logger.info(f"✅ Vector store: {vector_store.collection.count()} jobs indexed")
    logger.info(f"✅ New features: Job Coach · Market Insights · Interview Coach")
    logger.info("=" * 60)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)