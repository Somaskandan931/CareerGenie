"""
Progress Tracker service.
Tracks user progress across:
  - Learning Roadmap (week-by-week completion)
  - Portfolio Projects (status pipeline)
  - DSA Practice (LeetCode-style topic tracking)
  - Interview Pipeline (application → offer/reject funnel)

Backed by a simple JSON file store (swap for DB in production).
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Storage ───────────────────────────────────────────────────────────────────
_STORE_DIR = Path(os.getenv("PROGRESS_STORE_DIR", "/tmp/career_genie_progress"))
_STORE_DIR.mkdir(parents=True, exist_ok=True)


def _user_file(user_id: str) -> Path:
    return _STORE_DIR / f"{user_id}.json"


def _load(user_id: str) -> Dict:
    path = _user_file(user_id)
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception as e:
            logger.error(f"Error loading progress for {user_id}: {e}")
    return _empty_state(user_id)


def _save(user_id: str, state: Dict) -> None:
    state["updated_at"] = datetime.utcnow().isoformat()
    _user_file(user_id).write_text(json.dumps(state, indent=2))


def _empty_state(user_id: str) -> Dict:
    return {
        "user_id": user_id,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "roadmap": {},
        "roadmap_metadata": {},
        "projects": [],
        "dsa": {},
        "interviews": [],
        "activity_log": [],
    }


# ── Contribution heatmap helper ────────────────────────────────────────────────

def _log_activity(state: Dict, activity_type: str, count: int = 1) -> None:
    today = date.today().isoformat()
    log = state.setdefault("activity_log", [])
    for entry in log:
        if entry["date"] == today and entry["type"] == activity_type:
            entry["count"] += count
            return
    log.append({"date": today, "count": count, "type": activity_type})


# ── DSA topics seed ────────────────────────────────────────────────────────────

DSA_TOPICS = {
    "Arrays & Hashing": 30,
    "Two Pointers": 15,
    "Sliding Window": 12,
    "Stack": 15,
    "Binary Search": 18,
    "Linked List": 18,
    "Trees": 25,
    "Tries": 8,
    "Heap / Priority Queue": 12,
    "Backtracking": 14,
    "Graphs": 20,
    "Dynamic Programming": 30,
    "Greedy": 15,
    "Intervals": 8,
    "Math & Geometry": 10,
    "Bit Manipulation": 10,
}


# ── Interview pipeline stages ──────────────────────────────────────────────────

PIPELINE_STAGES = [
    "Applied",
    "OA / Assignment",
    "Technical Round 1",
    "Technical Round 2",
    "System Design",
    "HR Round",
    "Offer",
    "Rejected",
    "Withdrawn",
]


# ============================================================================
# PUBLIC API
# ============================================================================

class ProgressTracker:

    # ── USER STATE ─────────────────────────────────────────────────────────────

    def get_state(self, user_id: str) -> Dict:
        state = _load(user_id)
        # Seed DSA if empty
        if not state["dsa"]:
            state["dsa"] = {
                topic: {"solved": 0, "total": total, "problems": []}
                for topic, total in DSA_TOPICS.items()
            }
            _save(user_id, state)
        return state

    def get_summary(self, user_id: str) -> Dict:
        state = self.get_state(user_id)

        # Roadmap progress
        weeks = state.get("roadmap", {})
        total_tasks = sum(len(v) for v in weeks.values())
        done_tasks = sum(
            sum(1 for t in v if t.get("done")) for v in weeks.values()
        )

        # Project progress
        projects = state.get("projects", [])
        proj_by_status: Dict[str, int] = {}
        for p in projects:
            s = p.get("status", "Not Started")
            proj_by_status[s] = proj_by_status.get(s, 0) + 1

        # DSA progress
        dsa = state.get("dsa", {})
        dsa_solved = sum(v["solved"] for v in dsa.values())
        dsa_total = sum(v["total"] for v in dsa.values())

        # Interview funnel
        interviews = state.get("interviews", [])
        funnel: Dict[str, int] = {s: 0 for s in PIPELINE_STAGES}
        for iv in interviews:
            stage = iv.get("current_stage", "Applied")
            funnel[stage] = funnel.get(stage, 0) + 1

        offers = sum(1 for iv in interviews if iv.get("current_stage") == "Offer")
        rejections = sum(1 for iv in interviews if iv.get("current_stage") == "Rejected")

        return {
            "roadmap": {
                "total_tasks": total_tasks,
                "completed_tasks": done_tasks,
                "pct": round(done_tasks / total_tasks * 100, 1) if total_tasks else 0,
                "weeks_count": len(weeks),
                "metadata": state.get("roadmap_metadata", {})
            },
            "projects": {
                "total": len(projects),
                "by_status": proj_by_status,
            },
            "dsa": {
                "solved": dsa_solved,
                "total": dsa_total,
                "pct": round(dsa_solved / dsa_total * 100, 1) if dsa_total else 0,
                "by_topic": {
                    topic: {"solved": v["solved"], "total": v["total"]}
                    for topic, v in dsa.items()
                },
            },
            "interviews": {
                "total_applied": len(interviews),
                "offers": offers,
                "rejections": rejections,
                "active": len(interviews) - offers - rejections,
                "funnel": funnel,
                "success_rate": round(offers / len(interviews) * 100, 1) if interviews else 0,
            },
            "activity_log": state.get("activity_log", [])[-365:],  # last 365 days
        }

    # ── ROADMAP ────────────────────────────────────────────────────────────────

    def import_roadmap(self, user_id: str, roadmap: Dict) -> Dict:
        """Import a generated roadmap into the tracker with proper structure"""
        state = _load(user_id)

        # Validate roadmap structure
        if not roadmap:
            return {"error": "Invalid roadmap format - empty", "imported": 0}

        if 'phases' not in roadmap:
            return {"error": "Invalid roadmap format - missing phases", "imported": 0}

        weeks: Dict[str, List] = {}
        total_tasks = 0

        for phase in roadmap.get('phases', []):
            phase_title = phase.get('phase_title', 'Untitled Phase')
            phase_number = phase.get('phase_number', 1)

            for wt in phase.get('weekly_tasks', []):
                week_num = wt.get('week', 1)
                week_key = f"Week {week_num}"

                # Extract skills from resources or create from topic
                skills_covered = []
                for resource in wt.get('resources', []):
                    if isinstance(resource, dict) and 'skills' in resource:
                        skills_covered.extend(resource['skills'])

                # Create task with all necessary fields
                task = {
                    "id": str(uuid.uuid4()),
                    "topic": wt.get('topic', 'General'),
                    "description": wt.get('description', ''),
                    "milestone": wt.get('milestone', ''),
                    "hours": wt.get('hours_per_week', 8),
                    "phase": phase_title,
                    "phase_number": phase_number,
                    "week_number": week_num,
                    "done": False,
                    "done_at": None,
                    "resources": wt.get('resources', []),
                    "skills_covered": skills_covered or [wt.get('topic', '')],
                }

                weeks.setdefault(week_key, []).append(task)
                total_tasks += 1

        # Store with metadata
        state["roadmap"] = weeks
        state["roadmap_metadata"] = {
            "title": roadmap.get('title', 'Learning Roadmap'),
            "target_role": roadmap.get('target_role', ''),
            "duration_weeks": roadmap.get('duration_weeks', 12),
            "imported_at": datetime.utcnow().isoformat(),
            "total_tasks": total_tasks,
            "completed_tasks": 0,
            "summary": roadmap.get('summary', ''),
            "final_milestone": roadmap.get('final_milestone', ''),
            "tips": roadmap.get('tips', [])
        }

        _save(user_id, state)

        # Log activity
        _log_activity(state, "roadmap_imported", total_tasks)

        return {
            "imported": True,
            "weeks": len(weeks),
            "total_tasks": total_tasks,
            "metadata": state["roadmap_metadata"]
        }

    def get_roadmap_with_progress(self, user_id: str) -> Dict:
        """Get roadmap with progress tracking data"""
        state = _load(user_id)

        roadmap = state.get("roadmap", {})
        metadata = state.get("roadmap_metadata", {})

        # Calculate progress
        total_tasks = metadata.get("total_tasks", 0)
        completed_tasks = 0

        enriched_weeks = {}
        for week_key, tasks in roadmap.items():
            week_tasks = []
            week_completed = 0
            week_hours = 0

            for task in tasks:
                task_completed = task.get("done", False)
                if task_completed:
                    week_completed += 1
                    completed_tasks += 1

                week_hours += task.get("hours", 8)

                week_tasks.append({
                    **task,
                    "progress": "completed" if task_completed else "pending"
                })

            enriched_weeks[week_key] = {
                "tasks": week_tasks,
                "progress": {
                    "completed": week_completed,
                    "total": len(tasks),
                    "percentage": round(week_completed / len(tasks) * 100, 1) if tasks else 0,
                    "total_hours": week_hours,
                    "completed_hours": week_hours if week_completed == len(tasks) else 0
                }
            }

        # Calculate phase-wise progress
        phases_progress = {}
        for week_key, week_data in enriched_weeks.items():
            for task in week_data["tasks"]:
                phase = task.get("phase", "Unknown")
                if phase not in phases_progress:
                    phases_progress[phase] = {"total": 0, "completed": 0}
                phases_progress[phase]["total"] += 1
                if task.get("done"):
                    phases_progress[phase]["completed"] += 1

        # Add percentages to phases
        for phase, data in phases_progress.items():
            data["percentage"] = round(data["completed"] / data["total"] * 100, 1) if data["total"] else 0

        return {
            "metadata": {
                **metadata,
                "overall_progress": {
                    "completed": completed_tasks,
                    "total": total_tasks,
                    "percentage": round(completed_tasks / total_tasks * 100, 1) if total_tasks else 0
                },
                "phases_progress": phases_progress
            },
            "weeks": enriched_weeks
        }

    def update_task(self, user_id: str, week_key: str, task_id: str, done: bool) -> Dict:
        state = _load(user_id)
        weeks = state.get("roadmap", {})

        for task in weeks.get(week_key, []):
            if task["id"] == task_id:
                task["done"] = done
                task["done_at"] = datetime.utcnow().isoformat() if done else None

                # Update metadata completed count
                metadata = state.get("roadmap_metadata", {})
                if done:
                    metadata["completed_tasks"] = metadata.get("completed_tasks", 0) + 1
                else:
                    metadata["completed_tasks"] = max(0, metadata.get("completed_tasks", 0) - 1)

                if done:
                    _log_activity(state, "roadmap")

                _save(user_id, state)
                return {"updated": True, "task": task}

        return {"updated": False, "error": "Task not found"}

    # ── PROJECTS ───────────────────────────────────────────────────────────────

    PROJECT_STATUSES = [
        "Not Started", "In Progress", "Testing", "Deployed", "Completed"
    ]

    def add_project(self, user_id: str, project: Dict) -> Dict:
        state = _load(user_id)
        entry = {
            "id": project.get("id") or str(uuid.uuid4()),
            "title": project.get("title", "Untitled"),
            "tagline": project.get("tagline", ""),
            "tech_stack": project.get("tech_stack", []),
            "skills_covered": project.get("skills_covered", []),
            "difficulty": project.get("difficulty", "intermediate"),
            "estimated_weeks": project.get("estimated_weeks", 2),
            "status": "Not Started",
            "started_at": None,
            "completed_at": None,
            "github_url": None,
            "live_url": None,
            "notes": "",
            "progress_pct": 0,
        }
        state.setdefault("projects", []).append(entry)
        _save(user_id, state)
        return entry

    def update_project(self, user_id: str, project_id: str, updates: Dict) -> Dict:
        state = _load(user_id)
        for p in state.get("projects", []):
            if p["id"] == project_id:
                allowed = {"status", "github_url", "live_url", "notes", "progress_pct", "started_at", "completed_at"}
                for k, v in updates.items():
                    if k in allowed:
                        p[k] = v
                if updates.get("status") == "Completed" and not p.get("completed_at"):
                    p["completed_at"] = datetime.utcnow().isoformat()
                    _log_activity(state, "project")
                if updates.get("status") == "In Progress" and not p.get("started_at"):
                    p["started_at"] = datetime.utcnow().isoformat()
                _save(user_id, state)
                return p
        return {"error": "Project not found"}

    def import_projects(self, user_id: str, projects: List[Dict]) -> Dict:
        state = _load(user_id)
        state["projects"] = []
        for p in projects:
            self.add_project(user_id, p)
        return {"imported": len(projects)}

    # ── DSA ────────────────────────────────────────────────────────────────────

    def log_dsa_problem(self, user_id: str, topic: str, problem_name: str,
                         difficulty: str = "medium", solved: bool = True) -> Dict:
        state = self.get_state(user_id)
        topic_data = state["dsa"].setdefault(
            topic, {"solved": 0, "total": DSA_TOPICS.get(topic, 20), "problems": []}
        )
        # Avoid duplicates
        existing = [p for p in topic_data["problems"] if p["name"] == problem_name]
        if existing:
            existing[0]["solved"] = solved
        else:
            topic_data["problems"].append({
                "name": problem_name,
                "difficulty": difficulty,
                "solved": solved,
                "date": date.today().isoformat(),
            })
            if solved:
                topic_data["solved"] = min(topic_data["solved"] + 1, topic_data["total"])
        if solved:
            _log_activity(state, "dsa")
        _save(user_id, state)
        return topic_data

    def bulk_update_dsa(self, user_id: str, topic: str, solved_count: int) -> Dict:
        state = self.get_state(user_id)
        topic_data = state["dsa"].setdefault(
            topic, {"solved": 0, "total": DSA_TOPICS.get(topic, 20), "problems": []}
        )
        delta = max(0, solved_count - topic_data["solved"])
        topic_data["solved"] = min(solved_count, topic_data["total"])
        if delta > 0:
            _log_activity(state, "dsa", delta)
        _save(user_id, state)
        return topic_data

    # ── INTERVIEWS ─────────────────────────────────────────────────────────────

    def add_interview(self, user_id: str, company: str, role: str,
                       source: str = "LinkedIn") -> Dict:
        state = _load(user_id)
        entry = {
            "id": str(uuid.uuid4()),
            "company": company,
            "role": role,
            "source": source,
            "applied_date": date.today().isoformat(),
            "current_stage": "Applied",
            "stage_history": [
                {"stage": "Applied", "date": date.today().isoformat(), "notes": ""}
            ],
            "notes": "",
            "salary_offered": None,
            "outcome": None,  # "offer" | "rejected" | "withdrawn" | None (active)
        }
        state.setdefault("interviews", []).append(entry)
        _log_activity(state, "interview")
        _save(user_id, state)
        return entry

    def update_interview_stage(self, user_id: str, interview_id: str,
                                new_stage: str, notes: str = "") -> Dict:
        if new_stage not in PIPELINE_STAGES:
            return {"error": f"Invalid stage. Valid: {PIPELINE_STAGES}"}
        state = _load(user_id)
        for iv in state.get("interviews", []):
            if iv["id"] == interview_id:
                iv["current_stage"] = new_stage
                iv["stage_history"].append({
                    "stage": new_stage,
                    "date": date.today().isoformat(),
                    "notes": notes,
                })
                if new_stage in ("Offer", "Rejected", "Withdrawn"):
                    iv["outcome"] = new_stage.lower()
                    _log_activity(state, "interview_closed")
                _save(user_id, state)
                return iv
        return {"error": "Interview not found"}

    def delete_interview(self, user_id: str, interview_id: str) -> Dict:
        state = _load(user_id)
        before = len(state.get("interviews", []))
        state["interviews"] = [iv for iv in state.get("interviews", []) if iv["id"] != interview_id]
        _save(user_id, state)
        return {"deleted": before > len(state["interviews"])}

    def get_interview_analytics(self, user_id: str) -> Dict:
        state = _load(user_id)
        interviews = state.get("interviews", [])

        funnel: Dict[str, int] = {s: 0 for s in PIPELINE_STAGES}
        by_company: Dict[str, Dict] = {}
        by_source: Dict[str, int] = {}
        response_times = []

        for iv in interviews:
            stage = iv.get("current_stage", "Applied")
            funnel[stage] = funnel.get(stage, 0) + 1
            by_source[iv.get("source", "Unknown")] = by_source.get(iv.get("source", "Unknown"), 0) + 1

            # Time to first response (Applied → next stage)
            history = iv.get("stage_history", [])
            if len(history) >= 2:
                try:
                    d0 = date.fromisoformat(history[0]["date"])
                    d1 = date.fromisoformat(history[1]["date"])
                    response_times.append((d1 - d0).days)
                except Exception:
                    pass

        total = len(interviews)
        offers = funnel.get("Offer", 0)
        rejected = funnel.get("Rejected", 0)
        technical_reached = sum(
            funnel.get(s, 0) for s in ["Technical Round 1", "Technical Round 2", "System Design", "HR Round", "Offer"]
        )

        return {
            "total_applications": total,
            "funnel": funnel,
            "offers": offers,
            "rejections": rejected,
            "active": total - offers - rejected,
            "offer_rate": round(offers / total * 100, 1) if total else 0,
            "technical_conversion_rate": round(technical_reached / total * 100, 1) if total else 0,
            "avg_response_days": round(sum(response_times) / len(response_times), 1) if response_times else 0,
            "by_source": by_source,
            "pipeline_stages": PIPELINE_STAGES,
            "interviews": interviews,
        }


# Singleton
_tracker = None

def get_progress_tracker() -> ProgressTracker:
    global _tracker
    if _tracker is None:
        _tracker = ProgressTracker()
    return _tracker