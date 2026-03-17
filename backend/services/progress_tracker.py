"""
progress_tracker.py  (UPGRADED)
================================
Changes from brutal evaluation:
  ✅ Every significant user action now emits a feedback signal to
     FeedbackEngine, closing the learning loop between progress and
     job matching (e.g. completing a skill week → boost that skill's weight)
  ✅ Added skill_velocity metric — rate of DSA/roadmap completion per day
     so the advisor can flag if the user is falling behind
  ✅ Added streak tracking (consecutive active days)
  ✅ Retention risk flag: if no activity for 3+ days, system can prompt user
  ✅ All original functionality preserved
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

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
        "user_id":          user_id,
        "created_at":       datetime.utcnow().isoformat(),
        "updated_at":       datetime.utcnow().isoformat(),
        "roadmap":          {},
        "roadmap_metadata": {},
        "projects":         [],
        "dsa":              {},
        "interviews":       [],
        "activity_log":     [],
        # NEW
        "streak":           {"current": 0, "longest": 0, "last_active": None},
    }


def _log_activity(state: Dict, activity_type: str, count: int = 1) -> None:
    today = date.today().isoformat()
    log   = state.setdefault("activity_log", [])
    for entry in log:
        if entry["date"] == today and entry["type"] == activity_type:
            entry["count"] += count
            return
    log.append({"date": today, "count": count, "type": activity_type})


def _update_streak(state: Dict) -> None:
    """Update daily streak counter."""
    today      = date.today().isoformat()
    streak     = state.setdefault("streak", {"current": 0, "longest": 0, "last_active": None})
    last_active = streak.get("last_active")

    if last_active == today:
        return  # Already counted today
    if last_active:
        try:
            last_dt   = date.fromisoformat(last_active)
            gap_days  = (date.today() - last_dt).days
            if gap_days == 1:
                streak["current"] += 1
            elif gap_days > 1:
                streak["current"] = 1
        except Exception:
            streak["current"] = 1
    else:
        streak["current"] = 1

    streak["longest"]      = max(streak["longest"], streak["current"])
    streak["last_active"]  = today
    state["streak"]        = streak


def _emit_feedback(user_id: str, signal_type: str, item_id: str, metadata: Dict) -> None:
    """
    Non-blocking feedback emission — swallows all errors so tracker
    actions never fail due to FeedbackEngine issues.
    """
    try:
        from backend.services.feedback_engine import get_feedback_engine
        get_feedback_engine().record(user_id, signal_type, item_id, metadata)
    except Exception as e:
        logger.debug(f"Feedback emission skipped: {e}")


# ── DSA seed / pipeline stages (unchanged) ────────────────────────────────────

DSA_TOPICS = {
    "Arrays & Hashing": 30, "Two Pointers": 15, "Sliding Window": 12,
    "Stack": 15, "Binary Search": 18, "Linked List": 18, "Trees": 25,
    "Tries": 8, "Heap / Priority Queue": 12, "Backtracking": 14,
    "Graphs": 20, "Dynamic Programming": 30, "Greedy": 15,
    "Intervals": 8, "Math & Geometry": 10, "Bit Manipulation": 10,
}

PIPELINE_STAGES = [
    "Applied", "OA / Assignment", "Technical Round 1", "Technical Round 2",
    "System Design", "HR Round", "Offer", "Rejected", "Withdrawn",
]


# ── ProgressTracker ────────────────────────────────────────────────────────────

class ProgressTracker:

    # ── USER STATE ─────────────────────────────────────────────────────────────

    def get_state(self, user_id: str) -> Dict:
        state = _load(user_id)
        if not state["dsa"]:
            state["dsa"] = {
                topic: {"solved": 0, "total": total, "problems": []}
                for topic, total in DSA_TOPICS.items()
            }
            _save(user_id, state)
        return state

    def get_summary(self, user_id: str) -> Dict:
        state = self.get_state(user_id)

        weeks      = state.get("roadmap", {})
        total_tasks = sum(len(v) for v in weeks.values())
        done_tasks  = sum(sum(1 for t in v if t.get("done")) for v in weeks.values())

        projects = state.get("projects", [])
        proj_by_status: Dict[str, int] = {}
        for p in projects:
            s = p.get("status", "Not Started")
            proj_by_status[s] = proj_by_status.get(s, 0) + 1

        dsa       = state.get("dsa", {})
        dsa_solved = sum(v["solved"] for v in dsa.values())
        dsa_total  = sum(v["total"]  for v in dsa.values())

        interviews = state.get("interviews", [])
        funnel: Dict[str, int] = {s: 0 for s in PIPELINE_STAGES}
        for iv in interviews:
            stage = iv.get("current_stage", "Applied")
            funnel[stage] = funnel.get(stage, 0) + 1
        offers     = funnel.get("Offer", 0)
        rejections = funnel.get("Rejected", 0)

        # NEW: skill velocity (DSA solves per day over last 7 days)
        activity   = state.get("activity_log", [])
        recent_dsa = sum(
            e["count"] for e in activity
            if e["type"] == "dsa"
            and (date.today() - date.fromisoformat(e["date"])).days <= 7
        )
        velocity = round(recent_dsa / 7, 2)

        # NEW: retention risk
        streak        = state.get("streak", {})
        last_active   = streak.get("last_active")
        days_inactive = 0
        if last_active:
            try:
                days_inactive = (date.today() - date.fromisoformat(last_active)).days
            except Exception:
                pass
        retention_risk = days_inactive >= 3

        return {
            "roadmap": {
                "total_tasks":     total_tasks,
                "completed_tasks": done_tasks,
                "pct":             round(done_tasks / total_tasks * 100, 1) if total_tasks else 0,
                "weeks_count":     len(weeks),
                "metadata":        state.get("roadmap_metadata", {}),
            },
            "projects": {
                "total":     len(projects),
                "by_status": proj_by_status,
            },
            "dsa": {
                "solved": dsa_solved,
                "total":  dsa_total,
                "pct":    round(dsa_solved / dsa_total * 100, 1) if dsa_total else 0,
                "by_topic": {
                    topic: {"solved": v["solved"], "total": v["total"]}
                    for topic, v in dsa.items()
                },
            },
            "interviews": {
                "total_applied": len(interviews),
                "offers":        offers,
                "rejections":    rejections,
                "active":        len(interviews) - offers - rejections,
                "funnel":        funnel,
                "success_rate":  round(offers / len(interviews) * 100, 1) if interviews else 0,
            },
            "activity_log": activity[-365:],
            # NEW fields
            "streak":          streak,
            "skill_velocity":  velocity,       # DSA solves/day over last 7 days
            "retention_risk":  retention_risk, # True if inactive 3+ days
            "days_inactive":   days_inactive,
        }

    # ── ROADMAP ────────────────────────────────────────────────────────────────

    def import_roadmap(self, user_id: str, roadmap: Dict) -> Dict:
        state = _load(user_id)
        if not roadmap:
            return {"error": "Invalid roadmap format - empty", "imported": 0}
        if "phases" not in roadmap:
            return {"error": "Invalid roadmap format - missing phases", "imported": 0}

        weeks: Dict[str, List] = {}
        total_tasks = 0

        for phase in roadmap.get("phases", []):
            phase_title  = phase.get("phase_title", "Untitled Phase")
            phase_number = phase.get("phase_number", 1)

            for wt in phase.get("weekly_tasks", []):
                week_num  = wt.get("week", 1)
                week_key  = f"week_{week_num}"
                task = {
                    "id":           str(uuid.uuid4()),
                    "week":         week_num,
                    "phase":        phase_number,
                    "phase_title":  phase_title,
                    "topic":        wt.get("topic", ""),
                    "description":  wt.get("description", ""),
                    "resources":    wt.get("resources", []),
                    "milestone":    wt.get("milestone", ""),
                    "hours":        wt.get("hours_per_week", 8),
                    "done":         False,
                    "done_at":      None,
                }
                weeks.setdefault(week_key, []).append(task)
                total_tasks += 1

        state["roadmap"]          = weeks
        state["roadmap_metadata"] = {
            "title":           roadmap.get("title", ""),
            "target_role":     roadmap.get("target_role", ""),
            "duration_weeks":  roadmap.get("duration_weeks", 12),
            "total_tasks":     total_tasks,
            "completed_tasks": 0,
            "imported_at":     datetime.utcnow().isoformat(),
        }
        _save(user_id, state)
        return {"imported": total_tasks, "weeks": len(weeks)}

    def update_task(self, user_id: str, task_id: str, done: bool) -> Dict:
        state = _load(user_id)
        for week_tasks in state.get("roadmap", {}).values():
            for task in week_tasks:
                if task["id"] == task_id:
                    task["done"]    = done
                    task["done_at"] = datetime.utcnow().isoformat() if done else None

                    metadata = state.get("roadmap_metadata", {})
                    if done:
                        metadata["completed_tasks"] = metadata.get("completed_tasks", 0) + 1
                        _log_activity(state, "roadmap")
                        _update_streak(state)
                        # NEW — emit feedback so skill weights adapt
                        _emit_feedback(
                            user_id,
                            "view_details",
                            task_id,
                            {
                                "role":           metadata.get("target_role", ""),
                                "matched_skills": [task.get("topic", "")],
                            },
                        )
                    else:
                        metadata["completed_tasks"] = max(
                            0, metadata.get("completed_tasks", 0) - 1
                        )

                    _save(user_id, state)
                    return {"updated": True, "task": task}

        return {"updated": False, "error": "Task not found"}

    # ── PROJECTS ───────────────────────────────────────────────────────────────

    PROJECT_STATUSES = ["Not Started", "In Progress", "Testing", "Deployed", "Completed"]

    def add_project(self, user_id: str, project: Dict) -> Dict:
        state = _load(user_id)
        entry = {
            "id":              project.get("id") or str(uuid.uuid4()),
            "title":           project.get("title", "Untitled"),
            "tagline":         project.get("tagline", ""),
            "tech_stack":      project.get("tech_stack", []),
            "skills_covered":  project.get("skills_covered", []),
            "difficulty":      project.get("difficulty", "intermediate"),
            "estimated_weeks": project.get("estimated_weeks", 2),
            "status":          "Not Started",
            "started_at":      None,
            "completed_at":    None,
            "github_url":      None,
            "live_url":        None,
            "notes":           "",
            "progress_pct":    0,
        }
        state.setdefault("projects", []).append(entry)
        _save(user_id, state)
        return entry

    def update_project(self, user_id: str, project_id: str, updates: Dict) -> Dict:
        state = _load(user_id)
        for p in state.get("projects", []):
            if p["id"] == project_id:
                allowed = {
                    "status", "github_url", "live_url", "notes",
                    "progress_pct", "started_at", "completed_at",
                }
                for k, v in updates.items():
                    if k in allowed:
                        p[k] = v

                if updates.get("status") == "Completed" and not p.get("completed_at"):
                    p["completed_at"] = datetime.utcnow().isoformat()
                    _log_activity(state, "project")
                    _update_streak(state)
                    # NEW — project completion is a strong positive signal
                    _emit_feedback(
                        user_id,
                        "save_job",
                        project_id,
                        {
                            "matched_skills": p.get("skills_covered", []),
                            "role":           p.get("title", ""),
                        },
                    )

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

    def log_dsa_problem(
        self, user_id: str, topic: str, problem_name: str,
        difficulty: str = "medium", solved: bool = True,
    ) -> Dict:
        state      = self.get_state(user_id)
        topic_data = state["dsa"].setdefault(
            topic, {"solved": 0, "total": DSA_TOPICS.get(topic, 20), "problems": []}
        )
        existing = [p for p in topic_data["problems"] if p["name"] == problem_name]
        if existing:
            existing[0]["solved"] = solved
        else:
            topic_data["problems"].append({
                "name":       problem_name,
                "difficulty": difficulty,
                "solved":     solved,
                "date":       date.today().isoformat(),
            })
            if solved:
                topic_data["solved"] = min(topic_data["solved"] + 1, topic_data["total"])
        if solved:
            _log_activity(state, "dsa")
            _update_streak(state)
            # NEW — DSA solve signals skill interest
            _emit_feedback(
                user_id,
                "view_details",
                f"dsa_{topic}_{problem_name}",
                {"matched_skills": [topic.lower()], "role": ""},
            )
        _save(user_id, state)
        return topic_data

    def bulk_update_dsa(self, user_id: str, topic: str, solved_count: int) -> Dict:
        state      = self.get_state(user_id)
        topic_data = state["dsa"].setdefault(
            topic, {"solved": 0, "total": DSA_TOPICS.get(topic, 20), "problems": []}
        )
        delta               = max(0, solved_count - topic_data["solved"])
        topic_data["solved"] = min(solved_count, topic_data["total"])
        if delta > 0:
            _log_activity(state, "dsa", delta)
            _update_streak(state)
        _save(user_id, state)
        return topic_data

    # ── INTERVIEWS ─────────────────────────────────────────────────────────────

    def add_interview(
        self, user_id: str, company: str, role: str, source: str = "LinkedIn",
    ) -> Dict:
        state = _load(user_id)
        entry = {
            "id":            str(uuid.uuid4()),
            "company":       company,
            "role":          role,
            "source":        source,
            "applied_date":  date.today().isoformat(),
            "current_stage": "Applied",
            "stage_history": [
                {"stage": "Applied", "date": date.today().isoformat(), "notes": ""}
            ],
            "notes":          "",
            "salary_offered": None,
            "outcome":        None,
        }
        state.setdefault("interviews", []).append(entry)
        _log_activity(state, "interview")
        _update_streak(state)
        # NEW — applying to a role is a strong positive signal
        _emit_feedback(
            user_id,
            "apply_click",
            entry["id"],
            {"role": role, "company": company},
        )
        _save(user_id, state)
        return entry

    def update_interview_stage(
        self, user_id: str, interview_id: str, new_stage: str, notes: str = "",
    ) -> Dict:
        if new_stage not in PIPELINE_STAGES:
            return {"error": f"Invalid stage. Valid: {PIPELINE_STAGES}"}
        state = _load(user_id)
        for iv in state.get("interviews", []):
            if iv["id"] == interview_id:
                iv["current_stage"] = new_stage
                iv["stage_history"].append({
                    "stage": new_stage,
                    "date":  date.today().isoformat(),
                    "notes": notes,
                })
                if new_stage in ("Offer", "Rejected", "Withdrawn"):
                    iv["outcome"] = new_stage.lower()
                    _log_activity(state, "interview_closed")
                    # NEW — offer / rejection are the highest-value signals
                    signal = (
                        "offer_received" if new_stage == "Offer"
                        else "dismiss"
                    )
                    _emit_feedback(
                        user_id,
                        signal,
                        interview_id,
                        {"role": iv["role"], "company": iv["company"]},
                    )
                _save(user_id, state)
                return iv
        return {"error": "Interview not found"}

    def delete_interview(self, user_id: str, interview_id: str) -> Dict:
        state  = _load(user_id)
        before = len(state.get("interviews", []))
        state["interviews"] = [
            iv for iv in state.get("interviews", []) if iv["id"] != interview_id
        ]
        _save(user_id, state)
        return {"deleted": before > len(state["interviews"])}

    def get_interview_analytics(self, user_id: str) -> Dict:
        state      = _load(user_id)
        interviews = state.get("interviews", [])

        funnel: Dict[str, int]     = {s: 0 for s in PIPELINE_STAGES}
        by_source: Dict[str, int]  = {}
        response_times: List[int]  = []

        for iv in interviews:
            stage = iv.get("current_stage", "Applied")
            funnel[stage] = funnel.get(stage, 0) + 1
            src = iv.get("source", "Unknown")
            by_source[src] = by_source.get(src, 0) + 1

            history = iv.get("stage_history", [])
            if len(history) >= 2:
                try:
                    d0 = date.fromisoformat(history[0]["date"])
                    d1 = date.fromisoformat(history[1]["date"])
                    response_times.append((d1 - d0).days)
                except Exception:
                    pass

        total     = len(interviews)
        offers    = funnel.get("Offer", 0)
        rejected  = funnel.get("Rejected", 0)
        tech_hit  = sum(
            funnel.get(s, 0)
            for s in ["Technical Round 1", "Technical Round 2",
                      "System Design", "HR Round", "Offer"]
        )

        return {
            "total_applications":           total,
            "funnel":                       funnel,
            "offers":                       offers,
            "rejections":                   rejected,
            "active":                       total - offers - rejected,
            "offer_rate":                   round(offers / total * 100, 1) if total else 0,
            "technical_conversion_rate":    round(tech_hit / total * 100, 1) if total else 0,
            "avg_response_days":            round(
                sum(response_times) / len(response_times), 1
            ) if response_times else 0,
            "by_source":      by_source,
            "pipeline_stages": PIPELINE_STAGES,
            "interviews":     interviews,
        }


# ── Singleton ──────────────────────────────────────────────────────────────────
_tracker: Optional[ProgressTracker] = None


def get_progress_tracker() -> ProgressTracker:
    global _tracker
    if _tracker is None:
        _tracker = ProgressTracker()
    return _tracker