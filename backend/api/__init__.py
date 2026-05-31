"""
Career Genie API Module
=======================
FastAPI application and route registration.
"""

from backend.api.routes import (
    resume,
    jobs,
    roadmap,
    interview,
    coach,
    progress,
    mentor,
    insights,
    admin,
    auth,
)

__all__ = [
    "resume",
    "jobs",
    "roadmap",
    "interview",
    "coach",
    "progress",
    "mentor",
    "insights",
    "admin",
    "auth",
]