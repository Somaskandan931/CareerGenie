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
    ResumeUploadResponse,
    JobMatchRequest,
    JobMatchResponse,
    ConfigResponse,
    JobMatch,
)
from backend.services.resume_parser import resume_parser
from backend.services.vector_store import vector_store
from backend.services.matcher import get_job_matcher
from backend.services.career_advisor import career_advisor
from backend.services.job_scraper import get_job_scraper
from backend.services.roadmap_generator import get_roadmap_generator
from backend.services.project_generator import get_project_generator
from backend.services.tn_automotive_taxonomy import tn_extractor, NSQF_LEVELS, TN_SKILL_DB

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Career Genie – TN AUTO SkillBridge",
    description="AI-powered workforce skill gap analytics for Tamil Nadu Automotive & EV ecosystem",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


# ============================================================================
# CONFIG
# ============================================================================

@app.get("/config", response_model=ConfigResponse)
def get_config():
    return ConfigResponse(
        serpapi_key_present=bool(settings.SERPAPI_KEY),
        searchapi_key_present=bool(settings.SERPAPI_KEY),
        anthropic_key_present=bool(settings.ANTHROPIC_API_KEY),
        vector_db_initialized=True,
        total_indexed_jobs=vector_store.collection.count()
    )


# ============================================================================
# RESUME UPLOAD
# ============================================================================

@app.post("/upload-resume/parse", response_model=ResumeUploadResponse)
async def parse_resume(file: UploadFile = File(...)):
    logger.info(f"Received resume upload: {file.filename}")
    if not file.filename.lower().endswith(('.pdf', '.docx', '.doc')):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload PDF or DOCX.")
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        temp_path = tmp.name
    try:
        result = resume_parser.parse(temp_path)
        return ResumeUploadResponse(status="success", resume_text=result['resume_text'],
                                    word_count=result['word_count'])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {str(e)}")
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
                                    search_query=f"{request.job_query} in {request.location}", career_advice=None)
        try:
            from backend.services.job_filter import SmartJobFilter
            fe = SmartJobFilter()
            filtered = fe.filter_jobs(jobs, min_match_score=request.min_match_score,
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

        job_matches = [JobMatch(**m) for m in matches]
        resp = {"matched_jobs": job_matches, "total_jobs_fetched": len(jobs),
                "total_jobs_indexed": indexed_count,
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
        raise HTTPException(status_code=500, detail=f"Job matching failed: {str(e)}")


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
        raise HTTPException(status_code=500, detail=f"Roadmap generation failed: {str(e)}")


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
        raise HTTPException(status_code=500, detail=f"Project generation failed: {str(e)}")


# ============================================================================
# TN AUTOMOTIVE — SINGLE PROFILE
# ============================================================================

@app.post("/tn/analyze-profile")
def analyze_tn_profile(request: TNSkillAnalysisRequest):
    """
    Analyze a single ITI/polytechnic student profile.
    Extracts TN automotive skills, maps NSQF levels, and optionally
    compares against a specific job role.
    """
    extracted = tn_extractor.extract_skills(request.profile_text)
    result = {
        "extracted_skills": extracted,
        "total_skills_found": len(extracted),
        "nsqf_summary": _build_nsqf_summary(extracted),
        "role_analysis": None,
    }
    if request.target_role:
        result["role_analysis"] = tn_extractor.get_skill_gaps_for_role(extracted, request.target_role)
    return result


# ============================================================================
# TN AUTOMOTIVE — BATCH COHORT ANALYTICS
# ============================================================================

@app.post("/tn/batch-analytics")
def batch_analytics(request: BatchAnalysisRequest):
    """
    Analyze an entire batch of ITI/polytechnic student profiles.
    Returns cohort-level skill gap heatmap + per-student breakdowns.
    Designed for training officers and skill council administrators.
    """
    if not request.profiles:
        raise HTTPException(status_code=400, detail="No profiles provided")
    if len(request.profiles) > 500:
        raise HTTPException(status_code=400, detail="Maximum 500 profiles per batch")

    logger.info(f"Batch analytics: {len(request.profiles)} profiles — '{request.institution_name}'")
    profiles_dicts = [p.dict() for p in request.profiles]
    analytics = tn_extractor.batch_analyze(profiles_dicts)

    return {
        "institution": request.institution_name,
        "status": "success",
        **analytics,
    }


# ============================================================================
# TN AUTOMOTIVE — TAXONOMY METADATA
# ============================================================================

@app.get("/tn/roles")
def list_tn_roles():
    """All TN automotive job roles with required skills and clusters"""
    return {
        "roles": [
            {
                "role": name,
                "description": data["description"],
                "cluster": data["cluster"],
                "nsqf_target": data["nsqf_target"],
                "nsqf_target_label": NSQF_LEVELS[data["nsqf_target"]]["label"],
                "required_skills": data["required_skills"],
                "preferred_skills": data["preferred_skills"],
                "typical_employers": data["typical_employer"],
            }
            for name, data in tn_extractor.job_roles.items()
        ]
    }


@app.get("/tn/skills")
def list_tn_skills():
    """Full TN automotive skill taxonomy with NSQF levels and training sources"""
    return {
        "total_skills": len(TN_SKILL_DB),
        "skills": [
            {
                "skill": s["skill"],
                "category": s["category"],
                "sector": s["sector"],
                "nsqf_level": s["nsqf_level"],
                "nsqf_label": NSQF_LEVELS[s["nsqf_level"]]["label"],
                "training_sources": s["training_src"],
            }
            for s in TN_SKILL_DB
        ],
        "nsqf_levels": NSQF_LEVELS,
    }


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
            "roadmap_generator": "ok" if settings.ANTHROPIC_API_KEY else "missing_api_key",
            "project_generator": "ok" if settings.ANTHROPIC_API_KEY else "missing_api_key",
            "tn_automotive_taxonomy": f"ok — {len(tn_extractor.skill_db)} skills, {len(tn_extractor.job_roles)} roles",
        }
    }


# ============================================================================
# HELPERS
# ============================================================================

def _build_nsqf_summary(extracted_skills: List[Dict]) -> Dict:
    if not extracted_skills:
        return {"peak_level": 1, "peak_label": NSQF_LEVELS[1]["label"], "distribution": {}}
    dist: Dict[int, List[str]] = {}
    for s in extracted_skills:
        lvl = s["nsqf_level"]
        dist.setdefault(lvl, []).append(s["skill"])
    peak = max(dist.keys())
    return {
        "peak_level": peak,
        "peak_label": NSQF_LEVELS[peak]["label"],
        "distribution": {NSQF_LEVELS[lvl]["label"]: skills for lvl, skills in sorted(dist.items())},
    }


# ============================================================================
# STARTUP
# ============================================================================

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("Career Genie – TN AUTO SkillBridge v2.0 starting...")
    logger.info("=" * 60)
    Path(settings.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
    errors = settings.validate()
    if errors:
        for err in errors:
            logger.error(f"  ❌ {err}")
    else:
        logger.info("✅ All configurations valid")
    logger.info(f"✅ TN taxonomy: {len(tn_extractor.skill_db)} skills · {len(tn_extractor.job_roles)} roles")
    logger.info(f"✅ Vector store: {vector_store.collection.count()} jobs indexed")
    logger.info("=" * 60)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)