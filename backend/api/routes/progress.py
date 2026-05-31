"""
Progress API Routes
===================
Endpoints for progress tracking, roadmap management, and interview tracking.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator

from backend.core.logging import get_logger

logger = get_logger("routes.progress")

router = APIRouter(prefix="/progress", tags=["Progress"])


# ── Strict Response Models (prevents frontend shape mismatches) ─────────────

class TaskSchema(BaseModel):
    id: str
    week: int = 0
    phase: Any = None
    phase_title: str = ""
    topic: str
    description: str = ""
    resources: List[Any] = []
    milestone: str = ""
    hours: int = 8
    done: bool = False
    done_at: Optional[str] = None

    class Config:
        extra = "allow"  # forward-compatible with new fields


class FullProgressResponse(BaseModel):
    """
    Contract between backend and frontend ProgressDashboard.

    roadmap values are ALWAYS List[TaskSchema] — never null, never a dict.
    This eliminates the `tasks.filter is not a function` crash class.
    """
    roadmap:      Dict[str, List[TaskSchema]] = {}
    projects:     List[Any] = []
    dsa:          Dict[str, Any] = {}
    interviews:   List[Any] = []
    activity_log: List[Any] = []
    streak:       Dict[str, Any] = {}


# ── Request Models ──────────────────────────────────────────────────────────────

class ImportRoadmapBody(BaseModel):
    user_id: str
    roadmap: Dict


class TaskUpdateBody(BaseModel):
    user_id: str
    week_key: str
    task_id: str
    done: bool


class ImportProjectsBody(BaseModel):
    user_id: str
    projects: List[Dict]


class ProjectUpdateBody(BaseModel):
    user_id: str
    project_id: str
    updates: Optional[Dict] = None
    status: Optional[str] = None
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    progress_pct: Optional[int] = None
    notes: Optional[str] = None


class BulkUpdateDSARequest(BaseModel):
    user_id: str
    topic: str
    solved_count: int


class AddInterviewRequest(BaseModel):
    user_id: str
    company: str
    role: str
    source: str = "LinkedIn"


class UpdateInterviewStageRequest(BaseModel):
    user_id: str
    interview_id: str
    new_stage: str
    notes: str = ""


class FeedbackBody(BaseModel):
    user_id: str
    signal_type: str
    item_id: str
    metadata: Optional[Dict] = None


class RankingPreferenceBody(BaseModel):
    user_id: str
    winner: Dict
    loser: Dict
    context: Optional[Dict] = None


# ── Routes ──────────────────────────────────────────────────────────────────────

@router.get("/{user_id}/summary")
@router.get("/{user_id}")
async def get_progress_summary(user_id: str):
    """Get progress summary for a user."""
    try:
        from backend.services.progress_tracker import get_progress_tracker
        tracker = get_progress_tracker()
        return tracker.get_summary(user_id)
    except Exception as e:
        logger.error(f"Progress summary error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/full", response_model=FullProgressResponse)
async def get_progress_full(user_id: str):
    """
    Get full raw progress data for the dashboard frontend.

    Returns roadmap as { week_key: [task, ...] } arrays — never null or
    nested objects — so the frontend can safely call .filter() / .map().
    """
    try:
        from backend.services.progress_tracker import get_progress_tracker
        tracker = get_progress_tracker()
        return tracker.get_full(user_id)
    except Exception as e:
        logger.error(f"Progress full error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/interviews/analytics")
async def get_interview_analytics(user_id: str):
    """Get interview analytics for a user."""
    try:
        from backend.services.progress_tracker import get_progress_tracker
        tracker = get_progress_tracker()
        if hasattr(tracker, "get_interview_analytics"):
            return tracker.get_interview_analytics(user_id)
        summary = tracker.get_summary(user_id)
        return {"interviews": summary.get("interviews", [])}
    except Exception as e:
        logger.error(f"Interview analytics error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/roadmap/import")
async def import_roadmap(body: ImportRoadmapBody):
    """Import a roadmap into progress tracking."""
    try:
        from backend.services.progress_tracker import get_progress_tracker
        tracker = get_progress_tracker()
        return tracker.import_roadmap(body.user_id, body.roadmap)
    except Exception as e:
        logger.error(f"Roadmap import error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/roadmap/task/update")
@router.post("/task/update")
async def update_task(body: TaskUpdateBody):
    """Update task completion status."""
    try:
        from backend.services.progress_tracker import get_progress_tracker
        tracker = get_progress_tracker()
        return tracker.update_task(body.user_id, body.week_key, body.task_id, body.done)
    except Exception as e:
        logger.error(f"Task update error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/import")
async def import_projects(body: ImportProjectsBody):
    """Import projects into progress tracking."""
    try:
        from backend.services.progress_tracker import get_progress_tracker
        tracker = get_progress_tracker()
        if hasattr(tracker, "import_projects"):
            return tracker.import_projects(body.user_id, body.projects)
        return {"status": "ok", "imported": len(body.projects)}
    except Exception as e:
        logger.error(f"Projects import error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/projects/update")
async def update_project(body: ProjectUpdateBody):
    """Update project progress."""
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
        logger.error(f"Project update error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dsa/bulk-update")
@router.post("/dsa/log")
async def bulk_update_dsa(body: BulkUpdateDSARequest):
    """Bulk update DSA problems solved."""
    try:
        from backend.services.progress_tracker import get_progress_tracker
        tracker = get_progress_tracker()
        if hasattr(tracker, "bulk_update_dsa"):
            return tracker.bulk_update_dsa(body.user_id, body.topic, body.solved_count)
        for i in range(body.solved_count):
            tracker.log_dsa_problem(body.user_id, body.topic, f"problem_{i+1}", "medium", True)
        return {"status": "ok", "logged": body.solved_count}
    except Exception as e:
        logger.error(f"DSA bulk update error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interviews/add")
@router.post("/interview/add")
async def add_interview(body: AddInterviewRequest):
    """Add a new interview to tracking."""
    try:
        from backend.services.progress_tracker import get_progress_tracker
        tracker = get_progress_tracker()
        return tracker.add_interview(body.user_id, body.company, body.role, body.source)
    except Exception as e:
        logger.error(f"Interview add error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/interviews/stage")
async def update_interview_stage(body: UpdateInterviewStageRequest):
    """Update interview stage."""
    try:
        from backend.services.progress_tracker import get_progress_tracker
        tracker = get_progress_tracker()
        if hasattr(tracker, "update_interview_stage"):
            return tracker.update_interview_stage(body.user_id, body.interview_id, body.new_stage, body.notes)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Interview stage update error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/interviews/{user_id}/{interview_id}")
async def delete_interview(user_id: str, interview_id: str):
    """Delete an interview from tracking."""
    try:
        from backend.services.progress_tracker import get_progress_tracker
        tracker = get_progress_tracker()
        if hasattr(tracker, "delete_interview"):
            return tracker.delete_interview(user_id, interview_id)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Interview delete error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback/record")
async def record_feedback(body: FeedbackBody):
    """Record user feedback for personalization."""
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
        logger.error(f"Feedback record error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/stats/{user_id}")
async def feedback_stats(user_id: str):
    """Get feedback statistics for a user."""
    try:
        from backend.services.feedback_engine import get_feedback_engine
        engine = get_feedback_engine()
        return engine.get_stats(user_id)
    except Exception as e:
        logger.error(f"Feedback stats error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ranking/preference")
async def record_ranking_preference(body: RankingPreferenceBody):
    """Record user preference for learning-to-rank."""
    try:
        from backend.services.learning_to_rank import get_ltr_engine
        engine = get_ltr_engine()
        return engine.record_preference(
            user_id=body.user_id,
            winner=body.winner,
            loser=body.loser,
            context=body.context,
        )
    except Exception as e:
        logger.error(f"Ranking preference error: {e}", exc_info=True)
        return {"status": "skipped", "reason": str(e)}