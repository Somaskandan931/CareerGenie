"""
Progress Store service.
Persistent JSON-backed store for:
  - DSA problems
  - Roadmap checkpoints
  - Portfolio projects
  - Interview pipeline

All data is stored per-application (not per-user) in a single JSON file.
Swap the _load / _save helpers for a real DB in production.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# ── Storage ────────────────────────────────────────────────────────────────────
_STORE_FILE = Path(os.getenv("PROGRESS_STORE_FILE", "/tmp/career_genie_progress_store.json"))


def _load() -> Dict:
    if _STORE_FILE.exists():
        try:
            return json.loads(_STORE_FILE.read_text())
        except Exception:
            pass
    return _empty_state()


def _save(state: Dict) -> None:
    state["updated_at"] = datetime.utcnow().isoformat()
    _STORE_FILE.write_text(json.dumps(state, indent=2))


def _empty_state() -> Dict:
    return {
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "dsa_problems": [],        # List[DSAProblem dicts]
        "roadmap_checkpoints": [], # List[checkpoint dicts]
        "projects": [],            # List[project dicts]
        "interviews": [],          # List[interview dicts]
    }


# ── Helpers ────────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _today_iso() -> str:
    return date.today().isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


# ==============================================================================
# PROGRESS STORE CLASS
# ==============================================================================

class ProgressStore:

    # ── DSA ────────────────────────────────────────────────────────────────────

    def get_all_dsa(self) -> List[Dict]:
        """Return all DSA problems."""
        return _load().get("dsa_problems", [])

    def upsert_dsa_problem(self, problem: Dict) -> Dict:
        """
        Add a new DSA problem or update an existing one (matched by problem_id).
        Auto-generates problem_id if not provided.
        """
        state = _load()
        problems = state.setdefault("dsa_problems", [])

        pid = problem.get("problem_id") or _new_id()
        problem["problem_id"] = pid

        # Update existing
        for i, p in enumerate(problems):
            if p.get("problem_id") == pid:
                problems[i] = {**p, **problem, "updated_at": _now_iso()}
                _save(state)
                return problems[i]

        # Insert new
        problem.setdefault("created_at", _now_iso())
        problem["updated_at"] = _now_iso()
        problems.append(problem)
        _save(state)
        return problem

    def update_dsa_progress(self, problem_id: str, solved: bool,
                             attempts: Optional[int] = None,
                             notes: Optional[str] = None) -> Optional[Dict]:
        """Mark a DSA problem solved/unsolved. Returns updated problem or None."""
        state = _load()
        for p in state.get("dsa_problems", []):
            if p.get("problem_id") == problem_id:
                p["solved"] = solved
                p["updated_at"] = _now_iso()
                if attempts is not None:
                    p["attempts"] = attempts
                if notes is not None:
                    p["notes"] = notes
                if solved and not p.get("solved_at"):
                    p["solved_at"] = _today_iso()
                _save(state)
                return p
        return None

    # ── ROADMAP ────────────────────────────────────────────────────────────────

    def get_roadmap_progress(self, roadmap_id: str) -> List[Dict]:
        """Return all checkpoints for a given roadmap_id."""
        state = _load()
        return [
            c for c in state.get("roadmap_checkpoints", [])
            if c.get("roadmap_id") == roadmap_id
        ]

    def update_roadmap_checkpoint(self, roadmap_id: str, phase_number: int,
                                   week_number: int, completed: bool,
                                   hours_logged: float = 0.0,
                                   notes: str = "") -> Dict:
        """
        Upsert a roadmap checkpoint (matched by roadmap_id + phase + week).
        """
        state = _load()
        checkpoints = state.setdefault("roadmap_checkpoints", [])

        for c in checkpoints:
            if (c.get("roadmap_id") == roadmap_id
                    and c.get("phase_number") == phase_number
                    and c.get("week_number") == week_number):
                c["completed"] = completed
                c["hours_logged"] = hours_logged
                c["notes"] = notes
                c["updated_at"] = _now_iso()
                if completed and not c.get("completed_at"):
                    c["completed_at"] = _today_iso()
                _save(state)
                return c

        # New checkpoint
        entry = {
            "id": _new_id(),
            "roadmap_id": roadmap_id,
            "phase_number": phase_number,
            "week_number": week_number,
            "completed": completed,
            "hours_logged": hours_logged,
            "notes": notes,
            "completed_at": _today_iso() if completed else None,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }
        checkpoints.append(entry)
        _save(state)
        return entry

    # ── PROJECTS ───────────────────────────────────────────────────────────────

    def get_all_projects(self) -> List[Dict]:
        """Return all portfolio projects."""
        return _load().get("projects", [])

    def upsert_project(self, project: Dict) -> Dict:
        """
        Add a new project or update an existing one (matched by project_id).
        Auto-generates project_id if not provided.
        """
        state = _load()
        projects = state.setdefault("projects", [])

        pid = project.get("project_id") or _new_id()
        project["project_id"] = pid

        for i, p in enumerate(projects):
            if p.get("project_id") == pid:
                projects[i] = {**p, **project, "updated_at": _now_iso()}
                _save(state)
                return projects[i]

        project.setdefault("status", "Not Started")
        project.setdefault("progress_percent", 0)
        project.setdefault("milestones", [])
        project.setdefault("created_at", _now_iso())
        project["updated_at"] = _now_iso()
        projects.append(project)
        _save(state)
        return project

    def update_project(self, project_id: str,
                        status: Optional[str] = None,
                        github_url: Optional[str] = None,
                        live_url: Optional[str] = None,
                        progress_percent: Optional[int] = None,
                        milestone_done: Optional[str] = None,
                        notes: Optional[str] = None) -> Optional[Dict]:
        """Partially update a project. Returns updated project or None."""
        state = _load()
        for p in state.get("projects", []):
            if p.get("project_id") == project_id:
                if status is not None:
                    p["status"] = status
                    if status == "In Progress" and not p.get("started_at"):
                        p["started_at"] = _today_iso()
                    if status == "Completed" and not p.get("completed_at"):
                        p["completed_at"] = _today_iso()
                if github_url is not None:
                    p["github_url"] = github_url
                if live_url is not None:
                    p["live_url"] = live_url
                if progress_percent is not None:
                    p["progress_percent"] = progress_percent
                if notes is not None:
                    p["notes"] = notes
                if milestone_done:
                    milestones = p.setdefault("milestones_done", [])
                    if milestone_done not in milestones:
                        milestones.append(milestone_done)
                p["updated_at"] = _now_iso()
                _save(state)
                return p
        return None

    # ── INTERVIEWS ─────────────────────────────────────────────────────────────

    def get_all_interviews(self) -> List[Dict]:
        """Return all interview entries."""
        return _load().get("interviews", [])

    def create_interview(self, company: str, role: str,
                          job_url: str = "", applied_at: str = "") -> Dict:
        """Create a new interview / job application entry."""
        state = _load()
        entry = {
            "interview_id": _new_id(),
            "company": company,
            "role": role,
            "job_url": job_url,
            "applied_at": applied_at or _today_iso(),
            "current_stage": "Applied",
            "rounds": [],
            "final_outcome": None,       # "offer" | "rejected" | "withdrawn" | None
            "offer_details": None,
            "notes": "",
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }
        state.setdefault("interviews", []).append(entry)
        _save(state)
        return entry

    def add_interview_round(self, interview_id: str, round_data: Dict) -> Optional[Dict]:
        """
        Add a new round dict to an existing interview entry.
        Returns updated interview or None if not found.
        """
        state = _load()
        for iv in state.get("interviews", []):
            if iv.get("interview_id") == interview_id:
                round_data.setdefault("added_at", _now_iso())
                iv.setdefault("rounds", []).append(round_data)
                iv["updated_at"] = _now_iso()
                _save(state)
                return iv
        return None

    def update_interview_outcome(self, interview_id: str, final_outcome: str,
                                  offer_details: Optional[Dict] = None,
                                  notes: str = "") -> Optional[Dict]:
        """
        Set the final outcome of an interview process.
        Returns updated interview or None if not found.
        """
        state = _load()
        for iv in state.get("interviews", []):
            if iv.get("interview_id") == interview_id:
                iv["final_outcome"] = final_outcome
                iv["current_stage"] = final_outcome.capitalize()
                if offer_details:
                    iv["offer_details"] = offer_details
                if notes:
                    iv["notes"] = notes
                iv["closed_at"] = _today_iso()
                iv["updated_at"] = _now_iso()
                _save(state)
                return iv
        return None

    # ── SUMMARY ────────────────────────────────────────────────────────────────

    def get_summary(self) -> Dict:
        """Aggregated dashboard summary across all sections."""
        state = _load()

        # DSA
        problems = state.get("dsa_problems", [])
        dsa_solved = sum(1 for p in problems if p.get("solved"))

        # Roadmap
        checkpoints = state.get("roadmap_checkpoints", [])
        roadmap_done = sum(1 for c in checkpoints if c.get("completed"))

        # Projects
        projects = state.get("projects", [])
        proj_by_status: Dict[str, int] = {}
        for p in projects:
            s = p.get("status", "Not Started")
            proj_by_status[s] = proj_by_status.get(s, 0) + 1

        # Interviews
        interviews = state.get("interviews", [])
        offers = sum(1 for iv in interviews if iv.get("final_outcome") == "offer")
        rejected = sum(1 for iv in interviews if iv.get("final_outcome") == "rejected")

        return {
            "dsa": {
                "total": len(problems),
                "solved": dsa_solved,
                "unsolved": len(problems) - dsa_solved,
            },
            "roadmap": {
                "total_checkpoints": len(checkpoints),
                "completed": roadmap_done,
                "pct": round(roadmap_done / len(checkpoints) * 100, 1) if checkpoints else 0,
            },
            "projects": {
                "total": len(projects),
                "by_status": proj_by_status,
                "completed": proj_by_status.get("Completed", 0),
            },
            "interviews": {
                "total": len(interviews),
                "offers": offers,
                "rejected": rejected,
                "active": len(interviews) - offers - rejected,
                "offer_rate": round(offers / len(interviews) * 100, 1) if interviews else 0,
            },
        }


# Singleton
progress_store = ProgressStore()