"""
Career Genie AI - Main FastAPI Application
==========================================
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

# ✅ CREATE FASTAPI APP EARLY (before heavy imports)
from fastapi import FastAPI, Request, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader

from backend.core.logging import setup_logging, get_logger
from backend.core.config import settings

setup_logging(level=settings.LOG_LEVEL, use_color=True)
logger = get_logger("main")

# Admin API key guard
_ADMIN_KEY_HEADER = APIKeyHeader(name="X-Admin-Key", auto_error=False)
_ADMIN_API_KEY: str | None = os.getenv("ADMIN_API_KEY")

# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Career Genie AI starting…")
    settings.ensure_directories()

    for warning in settings.validate_config():
        logger.warning(f"⚠️  {warning}")

    # Lazy import to avoid loading at module level
    try:
        from backend.services.vector_store import vector_store
        if vector_store is not None:
            stats = vector_store.get_stats()
            logger.info(f"📚 Vector store ready: {stats['total_jobs']} jobs")
        else:
            logger.warning("⚠️  Vector store unavailable — job matching degraded")
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

    if not _ADMIN_API_KEY:
        logger.warning("⚠️  ADMIN_API_KEY not set — admin endpoints disabled")

    logger.info("✅ Career Genie AI ready")
    yield
    logger.info("👋 Career Genie AI shutting down")


async def require_admin(api_key: str | None = Security(_ADMIN_KEY_HEADER)):
    """Dependency: blocks requests that don't carry a valid admin key."""
    if not _ADMIN_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Admin API key not configured on server. Set ADMIN_API_KEY in .env.",
        )
    if api_key != _ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing X-Admin-Key header.")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Career Genie AI API",
    description="AI-powered career development platform",
    version="3.2.0",
    lifespan=lifespan,
)

# ── Rate limiting (must be added BEFORE CORS) ──────────────────────────────────
from backend.api.middleware.rate_limit import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)

# ── CORS ──────────────────────────────────────────────────────────────────────
_cors_origins = settings.cors_origins

if "*" in _cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r".*",
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ── Route registration (imported AFTER app creation) ───────────────────────

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

# Public routes
for router in [
    resume_router, jobs_router, roadmap_router, interview_router,
    coach_router, progress_router, mentor_router, insights_router,
    auth_router,
]:
    app.include_router(router)
    app.include_router(router, prefix="/api/v1")

# Admin routes — protected by require_admin dependency
app.include_router(admin_router, dependencies=[])
from fastapi import Depends
app.include_router(
    admin_router,
    prefix="/api/v1",
    dependencies=[Depends(require_admin)],
)
app.include_router(
    admin_router,
    dependencies=[Depends(require_admin)],
)


# ── URL aliases (frontend compatibility) ──────────────────────────────────────

from fastapi import File, UploadFile
from backend.api.routes.resume import parse_resume as _parse_resume_handler

@app.post("/upload-resume/parse")
async def upload_resume_parse_alias(file: UploadFile = File(...)):
    """Alias: frontend posts here; delegates to /resume/parse."""
    return await _parse_resume_handler(file)


from backend.api.routes.resume import ATSRequest, score_resume as _ats_handler

@app.post("/ats/score")
async def ats_score_alias(request: ATSRequest):
    """Alias: frontend posts here; delegates to /resume/ats/score."""
    return await _ats_handler(request)


@app.get("/config")
async def config_alias():
    """Alias: frontend fetches /config; delegates to /admin/config."""
    from backend.api.routes.admin import get_config
    return await get_config()


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
        "version": "3.2.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Deep health check — verifies critical dependencies."""
    issues = []

    # Vector store (lazy loaded)
    try:
        from backend.services.vector_store import vector_store
        if vector_store is None:
            issues.append("vector_store: unavailable")
        else:
            vector_store.get_stats()
    except Exception as e:
        issues.append(f"vector_store: {e}")

    # At least one LLM provider
    from backend.core.config import settings as s
    if not s.GROQ_API_KEY and not s.ANTHROPIC_API_KEY and not s.GEMINI_API_KEY:
        try:
            from backend.services.ollama_service import get_ollama_service
            if not get_ollama_service().available:
                issues.append("llm: no providers available")
        except Exception:
            issues.append("llm: no providers available")

    if issues:
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "version": "3.2.0", "issues": issues},
        )

    return {"status": "healthy", "version": "3.2.0"}


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)  # reload=False for production