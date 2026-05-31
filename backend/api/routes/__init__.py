"""
Career Genie API Routes
=======================
All API route modules organized by feature domain.
"""

from backend.api.routes.resume import router as resume_router
from backend.api.routes.jobs import router as jobs_router
from backend.api.routes.roadmap import router as roadmap_router
from backend.api.routes.interview import router as interview_router
from backend.api.routes.coach import router as coach_router
from backend.api.routes.progress import router as progress_router
from backend.api.routes.mentor import router as mentor_router
from backend.api.routes.insights import router as insights_router
from backend.api.routes.admin import router as admin_router
from backend.api.routes.auth import router as auth_router

__all__ = [
    "resume_router",
    "jobs_router",
    "roadmap_router",
    "interview_router",
    "coach_router",
    "progress_router",
    "mentor_router",
    "insights_router",
    "admin_router",
    "auth_router",
]