"""
Career Genie Backend - Main Application
Fixed version with proper import handling
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Load environment variables at startup
env_path = backend_dir / ".env"
load_dotenv(dotenv_path=env_path)

# Verify critical env vars
searchapi_key = os.getenv("SEARCHAPI_KEY") or os.getenv("SERPAPI_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")

if not searchapi_key:
    logging.warning("⚠️  WARNING: No SEARCHAPI_KEY found!")
    logging.warning(f"Looked for .env at: {env_path}")
else:
    logging.info(f"✅ SearchAPI Key loaded: {searchapi_key[:10]}...")

if not anthropic_key:
    logging.warning("⚠️  WARNING: No ANTHROPIC_API_KEY found!")
    logging.warning("RAG explanations will use fallback mode")
else:
    logging.info(f"✅ Anthropic Key loaded: {anthropic_key[:15]}...")

# Import routers - try both import styles
try:
    # Try without 'backend' prefix first (when running from backend directory)
    from builder.router import router as builder_router
    from parser.router import router as parser_router
    from job_search.router import router as job_router
    from rag.router import router as rag_router
    logging.info("✅ Imported routers without 'backend' prefix")
except ImportError as e:
    logging.warning(f"Import without prefix failed: {e}")
    try:
        # Try with 'backend' prefix (when running from parent directory)
        from backend.builder.router import router as builder_router
        from backend.parser.router import router as parser_router
        from backend.job_search.router import router as job_router
        from backend.rag.router import router as rag_router
        logging.info("✅ Imported routers with 'backend' prefix")
    except ImportError as e2:
        logging.error(f"Failed to import routers: {e2}")
        raise

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Career Genie RAG",
    description="Real-Time Resume-to-Job Matching with RAG",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers

app.include_router(parser_router, prefix="/upload-resume/parse", tags=["Resume Parser"])
app.include_router(job_router, prefix="/search-jobs", tags=["Job Search"])
app.include_router(rag_router, prefix="/rag", tags=["RAG Matching"])


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("=" * 70)
    logger.info("Career Genie Backend Starting...")
    logger.info("=" * 70)
    logger.info(f"Environment file: {env_path}")
    logger.info(f"Environment file exists: {env_path.exists()}")
    logger.info(f"SearchAPI configured: {'Yes' if searchapi_key else 'No'}")
    logger.info(f"Anthropic configured: {'Yes' if anthropic_key else 'No'}")
    logger.info("=" * 70)


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Career Genie Backend Shutting Down...")


@app.get("/", summary="API Root")
async def root():
    """API documentation and endpoint list"""
    return {
        "message": "Career Genie RAG - Real-Time Job Matching",
        "version": "2.0.0",
        "status": "operational",
        "endpoints": {
            "real_time_rag": "/rag/match-realtime",
            "rag_from_store": "/rag/match",
            "rag_health": "/rag/health",
            "rag_stats": "/rag/stats",
            "parse_resume": "/upload-resume/parse",
            "build_resume": "/build-resume",
            "search_jobs": "/search-jobs"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "configuration": {
            "searchapi_enabled": bool(searchapi_key),
            "anthropic_enabled": bool(anthropic_key)
        }
    }


@app.get("/health", summary="Health Check")
async def health():
    """Basic health check"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "services": {
            "api": "operational",
            "searchapi": "configured" if searchapi_key else "not configured",
            "anthropic": "configured" if anthropic_key else "not configured"
        }
    }


@app.get("/config", summary="Configuration Status")
async def config_status():
    """Check configuration status"""
    return {
        "environment_file": str(env_path),
        "environment_file_exists": env_path.exists(),
        "searchapi_key_present": bool(searchapi_key),
        "anthropic_key_present": bool(anthropic_key),
        "searchapi_key_length": len(searchapi_key) if searchapi_key else 0,
        "anthropic_key_length": len(anthropic_key) if anthropic_key else 0,
        "python_path": sys.path[:3]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )