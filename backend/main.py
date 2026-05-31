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

Architecture:
- Routes are organized in backend/api/routes/
- Middleware in backend/api/middleware/
- Core services in backend/core/
- Business logic in backend/services/
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.middleware.trace import TraceIDMiddleware
from backend.api.middleware.rate_limit import RateLimitMiddleware
from backend.api.middleware.cors import CORSMiddlewareConfig
from backend.api.routes import (
    resume_router,
    jobs_router,
    roadmap_router,
    interview_router,
    coach_router,
    progress_router,
    mentor_router,
    insights_router,
    admin_router,
    auth_router,
)
from backend.core.config import settings
from backend.core.logging import setup_logging, get_logger

# Setup logging
setup_logging(level="INFO", use_color=True)
logger = get_logger("main")


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

# ─────────────────────────────────────────────────────────────────────────────
# MIDDLEWARE
# ─────────────────────────────────────────────────────────────────────────────

# Trace ID middleware (must be first for proper tracing)
app.add_middleware(TraceIDMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    **CORSMiddlewareConfig.get_config(),
)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# ─────────────────────────────────────────────────────────────────────────────
# ROUTE REGISTRATION
# ─────────────────────────────────────────────────────────────────────────────

app.include_router(resume_router, prefix="/api/v1")
app.include_router(jobs_router, prefix="/api/v1")
app.include_router(roadmap_router, prefix="/api/v1")
app.include_router(interview_router, prefix="/api/v1")
app.include_router(coach_router, prefix="/api/v1")
app.include_router(progress_router, prefix="/api/v1")
app.include_router(mentor_router, prefix="/api/v1")
app.include_router(insights_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")

# Legacy routes (without /api/v1 prefix for backward compatibility)
app.include_router(resume_router)
app.include_router(jobs_router)
app.include_router(roadmap_router)
app.include_router(interview_router)
app.include_router(coach_router)
app.include_router(progress_router)
app.include_router(mentor_router)
app.include_router(insights_router)
app.include_router(admin_router)
app.include_router(auth_router)


# ─────────────────────────────────────────────────────────────────────────────
# HEALTH AND ROOT ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """API root with endpoint documentation."""
    return {
        "name": "Career Genie AI API",
        "version": "3.0.0",
        "status": "operational",
        "endpoints": {
            "resume": "/upload-resume/parse",
            "ats": "/ats/score",
            "match": "/jobs/match",
            "roadmap": "/roadmap/generate",
            "interview": "/interview/generate-questions",
            "coach": "/coach/chat",
            "progress": "/progress/*",
            "mentor": "/mentor/search",
            "insights": "/insights/market",
        },
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "version": "3.0.0",
    }


# ─────────────────────────────────────────────────────────────────────────────
# EXCEPTION HANDLERS
# ─────────────────────────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return {
        "error": "internal_error",
        "message": "An unexpected error occurred. Please try again later.",
    }, 500


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