"""
Career Genie AI - Main FastAPI Application (Fixed)
===================================================
Key fixes vs original:
  - Added URL aliases that frontend expects:
      /upload-resume/parse  → resume parse
      /ats/score            → ATS scoring
      /config               → config (was /admin/config)
      /projects/suggest     → project suggestions
  - CareerGenieError → HTTP exception handler
  - Startup warnings for missing config
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.core.logging import setup_logging, get_logger
from backend.core.config import settings

setup_logging(level=settings.LOG_LEVEL, use_color=True)
logger = get_logger("main")


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Career Genie AI starting…")
    settings.ensure_directories()

    for warning in settings.validate_config():
        logger.warning(f"⚠️  {warning}")

    try:
        from backend.services.vector_store import vector_store
        stats = vector_store.get_stats()
        logger.info(f"📚 Vector store ready: {stats['total_jobs']} jobs")
    except Exception as e:
        logger.warning(f"⚠️  Vector store: {e}")

    try:
        from backend.services.ollama_service import get_ollama_service
        svc = get_ollama_service()
        if svc.available:
            logger.info(f"🤖 Ollama ready ({svc.llm_model})")
        else:
            logger.warning("⚠️  Ollama not running — cloud LLMs will be used")
    except Exception as e:
        logger.warning(f"⚠️  Ollama: {e}")

    logger.info("✅ Career Genie AI ready")
    yield
    logger.info("👋 Career Genie AI shutting down")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Career Genie AI API",
    description="AI-powered career development platform",
    version="3.1.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten in production via settings
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Route registration ────────────────────────────────────────────────────────

from backend.api.routes.resume    import router as resume_router
from backend.api.routes.jobs      import router as jobs_router
from backend.api.routes.roadmap   import router as roadmap_router
from backend.api.routes.interview import router as interview_router
from backend.api.routes.coach     import router as coach_router
from backend.api.routes.progress  import router as progress_router
from backend.api.routes.mentor    import router as mentor_router
from backend.api.routes.insights  import router as insights_router
from backend.api.routes.admin     import router as admin_router
from backend.api.routes.auth      import router as auth_router

for router in [
    resume_router, jobs_router, roadmap_router, interview_router,
    coach_router, progress_router, mentor_router, insights_router,
    admin_router, auth_router,
]:
    app.include_router(router)
    app.include_router(router, prefix="/api/v1")


# ── URL aliases (frontend compatibility) ──────────────────────────────────────

# Frontend calls /upload-resume/parse but router is /resume/parse
from fastapi import File, UploadFile
from backend.api.routes.resume import parse_resume as _parse_resume_handler

@app.post("/upload-resume/parse")
async def upload_resume_parse_alias(file: UploadFile = File(...)):
    """Alias: frontend posts here; delegates to /resume/parse."""
    return await _parse_resume_handler(file)


# Frontend calls /ats/score but router is /resume/ats/score
from backend.api.routes.resume import ATSRequest, score_resume as _ats_handler

@app.post("/ats/score")
async def ats_score_alias(request: ATSRequest):
    """Alias: frontend posts here; delegates to /resume/ats/score."""
    return await _ats_handler(request)


# Frontend fetches /config (was /admin/config)
@app.get("/config")
async def config_alias():
    """Alias: frontend fetches /config; delegates to /admin/config."""
    from backend.api.routes.admin import get_config
    return await get_config()


# Frontend calls /projects/suggest
@app.post("/projects/suggest")
async def projects_suggest_alias(request: Request):
    """Alias: project suggestions."""
    try:
        from backend.api.routes.roadmap import suggest_projects, ProjectRequest
        body = await request.json()
        req = ProjectRequest(**body)
        return await suggest_projects(req)
    except Exception as e:
        logger.error(f"projects/suggest alias error: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"detail": str(e)})


# ── Exception handlers ────────────────────────────────────────────────────────

from backend.core.exceptions import CareerGenieError

@app.exception_handler(CareerGenieError)
async def career_genie_error_handler(request: Request, exc: CareerGenieError):
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "message": "An unexpected error occurred."},
    )


# ── Health / root ─────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "name": "Career Genie AI API",
        "version": "3.1.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "3.1.0"}


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)