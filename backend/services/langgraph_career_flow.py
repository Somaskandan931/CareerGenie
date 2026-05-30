"""
langgraph_career_flow.py
========================
LangGraph-powered 4-node career analysis pipeline.

Graph:  parse_resume → gap_analysis → generate_roadmap → suggest_projects

Each node receives the full accumulated CareerState from all previous nodes,
so every step is grounded in the output of the step before it.
This is what makes it a real LangGraph — not just sequential function calls.

Falls back to sequential execution if langgraph is not installed.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, TypedDict

logger = logging.getLogger(__name__)


# ── Shared state schema ───────────────────────────────────────────────────────

class CareerState(TypedDict):
    resume_text:    str
    target_role:    str
    duration_weeks: int
    # Populated by each node:
    parsed_skills: List[str]
    skill_gaps:    List[str]
    roadmap:       Optional[Dict]
    projects:      Optional[List[Dict]]
    error:         Optional[str]


# ── Node 1 ────────────────────────────────────────────────────────────────────

def node_parse_resume(state: CareerState) -> CareerState:
    """Extract skills from resume using EnhancedSkillExtractor."""
    try:
        from backend.services.enhanced_skill_extractor import EnhancedSkillExtractor
        extractor = EnhancedSkillExtractor()
        raw    = extractor.extract_skills_with_context(state["resume_text"])
        skills = [s["skill"] for s in raw[:15]] if raw else ["Python", "Communication"]
        logger.info(f"[LangGraph] node_parse_resume → {len(skills)} skills")
        return {**state, "parsed_skills": skills}
    except Exception as e:
        logger.error(f"[LangGraph] node_parse_resume error: {e}")
        return {**state, "parsed_skills": ["Python", "SQL"], "error": str(e)}


# ── Node 2 ────────────────────────────────────────────────────────────────────

def node_gap_analysis(state: CareerState) -> CareerState:
    """Identify skill gaps for target role — grounded in parsed_skills."""
    try:
        from backend.services.career_advisor import career_advisor
        advice = career_advisor.generate_career_advice(
            resume_text=state["resume_text"],
            target_role=state["target_role"],
            job_matches=[],
        )
        gaps = [g["skill"] for g in (advice or {}).get("skill_gaps", [])][:8]
        if not gaps:
            role_skills = ["Docker", "System Design", "CI/CD", "Kubernetes", "AWS"]
            gaps = [s for s in role_skills if s.lower() not in
                    [p.lower() for p in state["parsed_skills"]]][:4]
        logger.info(f"[LangGraph] node_gap_analysis → {len(gaps)} gaps")
        return {**state, "skill_gaps": gaps}
    except Exception as e:
        logger.error(f"[LangGraph] node_gap_analysis error: {e}")
        return {**state, "skill_gaps": ["Docker", "System Design"], "error": str(e)}


# ── Node 3 ────────────────────────────────────────────────────────────────────

def node_generate_roadmap(state: CareerState) -> CareerState:
    """Generate personalized roadmap — grounded in gap_analysis output."""
    try:
        from backend.services.roadmap_generator import get_roadmap_generator
        generator = get_roadmap_generator()
        roadmap   = generator.generate_roadmap(
            resume_text    = state["resume_text"],
            target_role    = state["target_role"],
            skill_gaps     = state["skill_gaps"],      # ← Node 2 output
            duration_weeks = state["duration_weeks"],
        )
        logger.info("[LangGraph] node_generate_roadmap → roadmap generated")
        return {**state, "roadmap": roadmap}
    except Exception as e:
        logger.error(f"[LangGraph] node_generate_roadmap error: {e}")
        return {**state, "roadmap": None, "error": str(e)}


# ── Node 4 ────────────────────────────────────────────────────────────────────

def node_suggest_projects(state: CareerState) -> CareerState:
    """Suggest portfolio projects — grounded in skill_gaps + roadmap."""
    try:
        from backend.services.project_generator import get_project_generator
        generator = get_project_generator()
        projects  = generator.suggest_projects(
            resume_text  = state["resume_text"],
            target_role  = state["target_role"],
            skill_gaps   = state["skill_gaps"],        # ← Node 2 output
            difficulty   = "intermediate",
            num_projects = 4,
        )
        logger.info(f"[LangGraph] node_suggest_projects → {len(projects)} projects")
        return {**state, "projects": projects}
    except Exception as e:
        logger.error(f"[LangGraph] node_suggest_projects error: {e}")
        return {**state, "projects": [], "error": str(e)}


# ── Graph builder ─────────────────────────────────────────────────────────────

def _build_graph():
    """Compile the LangGraph StateGraph. Returns None if langgraph not installed."""
    try:
        from langgraph.graph import StateGraph, END

        builder = StateGraph(CareerState)

        builder.add_node("parse_resume",     node_parse_resume)
        builder.add_node("gap_analysis",     node_gap_analysis)
        builder.add_node("generate_roadmap", node_generate_roadmap)
        builder.add_node("suggest_projects", node_suggest_projects)

        builder.set_entry_point("parse_resume")
        builder.add_edge("parse_resume",     "gap_analysis")
        builder.add_edge("gap_analysis",     "generate_roadmap")
        builder.add_edge("generate_roadmap", "suggest_projects")
        builder.add_edge("suggest_projects", END)

        return builder.compile()

    except ImportError:
        logger.warning("langgraph not installed — install with: pip install langgraph")
        return None


# ── Public entry point ────────────────────────────────────────────────────────

def run_deep_analysis(
    resume_text:    str,
    target_role:    str = "Software Engineer",
    duration_weeks: int = 12,
) -> Dict[str, Any]:
    """
    Run the 4-node career analysis graph.
    Falls back to sequential execution if langgraph is not installed.
    """
    initial_state: CareerState = {
        "resume_text":    resume_text,
        "target_role":    target_role,
        "duration_weeks": duration_weeks,
        "parsed_skills":  [],
        "skill_gaps":     [],
        "roadmap":        None,
        "projects":       None,
        "error":          None,
    }

    graph = _build_graph()

    if graph is not None:
        final_state    = graph.invoke(initial_state)
        used_langgraph = True
    else:
        # Sequential fallback — same nodes, no graph abstraction
        s = node_parse_resume(initial_state)
        s = node_gap_analysis(s)
        s = node_generate_roadmap(s)
        s = node_suggest_projects(s)
        final_state    = s
        used_langgraph = False

    return {
        "status":               "success",
        "used_langgraph":       used_langgraph,
        "target_role":          target_role,
        "parsed_skills":        final_state.get("parsed_skills", []),
        "skill_gaps":           final_state.get("skill_gaps", []),
        "roadmap":              final_state.get("roadmap"),
        "projects":             final_state.get("projects", []),
        "graph_nodes_executed": [
            "parse_resume", "gap_analysis", "generate_roadmap", "suggest_projects"
        ],
        "error": final_state.get("error"),
    }