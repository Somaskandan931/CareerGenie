from __future__ import annotations
"""
Agent Orchestrator
==================
Replaces the "fake agentic system" critique.

Before : each service was a standalone LLM wrapper called independently.
After  : a lightweight orchestrator that:
  1. Decomposes user goals into a task plan
  2. Routes sub-tasks to specialised agents
  3. Lets agents share intermediate results (shared memory bus)
  4. Reflects on tool outputs and decides next action (ReAct-style loop)
  5. Synthesises a unified response

Agents registered here:
  - ResumeAgent   → parsing, ATS scoring, rewriting
  - JobAgent      → matching, filtering, market insights
  - InterviewAgent→ question generation, answer evaluation, mock interview
  - RoadmapAgent  → skill gap analysis, learning path, project suggestions
  - AdvisorAgent  → holistic career advice, progression planning

No external agent framework is required — the orchestrator is pure Python
with a Groq planner call at the top.
"""

import json
import logging
import re
import time
import uuid
from typing import Any, Callable, Dict, List, Optional


from backend.config import settings
from backend.services.llm import llm_call_sync, llm_call_smart_sync


logger = logging.getLogger(__name__)

# ── Shared memory bus ──────────────────────────────────────────────────────────

class AgentMemory:
    """
    In-process key-value store that all agents can read/write.
    Acts as the 'shared context' so agents don't operate in silos.
    """

    def __init__(self) -> None:
        self._store: Dict[str, Any] = {}
        self._trace: List[Dict] = []

    def set(self, key: str, value: Any, agent_name: str = "") -> None:
        self._store[key] = value
        self._trace.append({
            "op":    "write",
            "key":   key,
            "agent": agent_name,
            "ts":    time.time(),
        })

    def get(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default)

    def keys(self) -> List[str]:
        return list(self._store.keys())

    def trace(self) -> List[Dict]:
        return self._trace

    def snapshot(self) -> Dict:
        return dict(self._store)


# ── Base agent ─────────────────────────────────────────────────────────────────

class BaseAgent:
    """All concrete agents inherit from this."""

    name: str = "BaseAgent"

    def __init__(self, memory: AgentMemory) -> None:
        self.memory = memory

    def run(self, task: Dict) -> Dict:
        raise NotImplementedError

    def _call_llm(self, prompt: str, max_tokens: int = 800, temperature: float = 0.4) -> str:
        return llm_call_sync(
            system="You are an expert AI assistant. Respond clearly and concisely.",
            user=prompt,
            temp=temperature,
            max_tokens=max_tokens,
        )

    def _safe_json(self, raw: str) -> Any:
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"^```\s*",     "", raw)
        raw = re.sub(r"\s*```$",     "", raw)
        return json.loads(raw)


# ── Concrete agents ────────────────────────────────────────────────────────────

class ResumeAgent(BaseAgent):
    name = "ResumeAgent"

    def run(self, task: Dict) -> Dict:
        """
        Handles: ats_score, rewrite, extract_skills, parse_gaps
        """
        action   = task.get("action", "ats_score")
        resume   = self.memory.get("resume_text", "")
        role     = task.get("target_role", self.memory.get("target_role", "Software Engineer"))

        if not resume:
            return {"error": "No resume in memory. Load resume first."}

        if action == "ats_score":
            from backend.services.ats_scorer import ats_scorer
            result = ats_scorer.score_resume(resume, role)
            self.memory.set("ats_score", result, self.name)
            return result

        if action == "rewrite":
            from backend.services.resume_rewriter import resume_rewriter
            result = resume_rewriter.rewrite(resume, role)
            self.memory.set("rewritten_resume", result, self.name)
            return result

        if action == "extract_skills":
            from backend.services.enhanced_skill_extractor import EnhancedSkillExtractor
            extractor = EnhancedSkillExtractor()
            skills = extractor.extract_skills_with_context(resume)
            self.memory.set("resume_skills", skills, self.name)
            return {"skills": skills}

        if action == "parse_gaps":
            # Use LLM to identify skill gaps given resume + target role
            prompt = f"""Given this resume excerpt and target role, list the top 5 skill gaps.
Resume: {resume[:1500]}
Target role: {role}

Return ONLY a JSON array of strings: ["gap1", "gap2", ...]"""
            raw = self._call_llm(prompt, max_tokens=300)
            gaps = self._safe_json(raw)
            self.memory.set("skill_gaps", gaps, self.name)
            return {"skill_gaps": gaps}

        return {"error": f"Unknown action: {action}"}


class JobAgent(BaseAgent):
    name = "JobAgent"

    def run(self, task: Dict) -> Dict:
        """
        Handles: match, filter, market_insights, rank_with_feedback
        """
        action = task.get("action", "match")
        resume = self.memory.get("resume_text", "")

        if action == "match":
            from backend.services.matcher import get_job_matcher
            matcher = get_job_matcher()
            matches = matcher.match_resume_to_jobs(
                resume_text=resume,
                top_k=task.get("top_k", 10),
                location=task.get("location", "India"),
            )
            self.memory.set("job_matches", matches, self.name)
            return {"matches": matches}

        if action == "rank_with_feedback":
            # Re-rank existing matches using adaptive weights from FeedbackEngine
            matches  = self.memory.get("job_matches", [])
            user_id  = task.get("user_id", "")
            if not matches or not user_id:
                return {"error": "No matches or user_id available"}

            from backend.services.feedback_engine import get_feedback_engine
            engine = get_feedback_engine()

            ranked = []
            for job in matches:
                # Decompose existing score back into rough components
                # (real implementation stores per-component scores in the match)
                base = {
                    "semantic": job.get("semantic_score", job["match_score"] * 0.35),
                    "skills":   job.get("skills_score",   job["match_score"] * 0.45),
                    "title":    job.get("title_score",    job["match_score"] * 0.20),
                }
                personalised = engine.personalise_score(user_id, job, base)
                ranked.append({**job, "personalised_score": personalised})

            ranked.sort(key=lambda x: x["personalised_score"], reverse=True)
            self.memory.set("ranked_matches", ranked, self.name)
            return {"ranked_matches": ranked}

        if action == "filter":
            from backend.services.job_filter import SmartJobFilter
            flt   = SmartJobFilter()
            jobs  = self.memory.get("job_matches", [])
            filtered = flt.filter_jobs(
                jobs,
                min_match_score=task.get("min_score", 40),
                experience_level=task.get("experience_level"),
            )
            self.memory.set("filtered_jobs", filtered, self.name)
            return {"filtered_jobs": filtered}

        if action == "market_insights":
            from backend.services.market_insights import get_market_insights
            mi = get_market_insights()
            skills = [s["skill"] for s in self.memory.get("resume_skills", [])]
            role = task.get("role", self.memory.get("target_role", "Software Engineer"))
            result = mi.get_insights(role, skills)
            self.memory.set("market_insights", result, self.name)
            return result

        return {"error": f"Unknown action: {action}"}


class InterviewAgent(BaseAgent):
    name = "InterviewAgent"

    def run(self, task: Dict) -> Dict:
        action = task.get("action", "generate_questions")
        role   = task.get("role", self.memory.get("target_role", "Software Engineer"))
        resume = self.memory.get("resume_text", "")

        if action == "generate_questions":
            from backend.services.interview_coach import get_interview_coach
            coach = get_interview_coach()
            questions = coach.generate_questions(
                role=role,
                interview_type=task.get("interview_type", "mixed"),
                resume_text=resume,
                num_questions=task.get("num_questions", 10),
            )
            self.memory.set("interview_questions", questions, self.name)
            return {"questions": questions}

        if action == "evaluate_answer":
            from backend.services.interview_coach import get_interview_coach
            coach = get_interview_coach()
            result = coach.evaluate_answer(
                question=task["question"],
                answer=task["answer"],
                role=role,
            )
            # Accumulate evaluations
            evals = self.memory.get("interview_evals", [])
            evals.append({"question": task["question"], "evaluation": result})
            self.memory.set("interview_evals", evals, self.name)
            return result

        if action == "session_summary":
            # Summarise all evaluations into a coaching report
            evals = self.memory.get("interview_evals", [])
            if not evals:
                return {"error": "No evaluations recorded yet"}

            scores = [e["evaluation"].get("score", 5) for e in evals]
            avg_score = round(sum(scores) / len(scores), 1)
            weak_areas = [
                imp
                for e in evals
                for imp in e["evaluation"].get("improvements", [])
            ]

            prompt = f"""Summarise this mock interview performance in 3 sentences.
Average score: {avg_score}/10
Questions answered: {len(evals)}
Common improvement areas: {'; '.join(weak_areas[:6])}

Then list 3 targeted practice recommendations."""

            summary_text = self._call_llm(prompt, max_tokens=400)
            result = {
                "avg_score":    avg_score,
                "total_answered": len(evals),
                "narrative_summary": summary_text,
                "weak_areas": weak_areas[:6],
            }
            self.memory.set("interview_session_summary", result, self.name)
            return result

        return {"error": f"Unknown action: {action}"}


class RoadmapAgent(BaseAgent):
    name = "RoadmapAgent"

    def run(self, task: Dict) -> Dict:
        action = task.get("action", "generate")
        resume = self.memory.get("resume_text", "")
        role   = task.get("target_role", self.memory.get("target_role", "Software Engineer"))
        gaps   = self.memory.get("skill_gaps", task.get("skill_gaps", []))

        if action == "generate":
            from backend.services.roadmap_generator import get_roadmap_generator
            gen = get_roadmap_generator()
            roadmap = gen.generate_roadmap(
                resume_text=resume,
                target_role=role,
                skill_gaps=gaps,
                duration_weeks=task.get("duration_weeks", 12),
            )
            self.memory.set("roadmap", roadmap, self.name)
            return roadmap

        if action == "suggest_projects":
            from backend.services.project_generator import get_project_generator
            gen = get_project_generator()
            projects = gen.suggest_projects(
                resume_text=resume,
                target_role=role,
                skill_gaps=gaps,
                difficulty=task.get("difficulty", "intermediate"),
            )
            self.memory.set("suggested_projects", projects, self.name)
            return {"projects": projects}

        if action == "refine_with_feedback":
            """
            Re-prioritise roadmap topics based on which skills the user has
            shown interest in (from feedback engine profile).
            """
            user_id = task.get("user_id", "")
            roadmap = self.memory.get("roadmap", {})
            if not user_id or not roadmap:
                return {"error": "Need user_id and roadmap in memory"}

            from backend.services.feedback_engine import get_feedback_engine
            profile = get_feedback_engine().get_profile(user_id)
            skill_interest = profile.get("skill_interest", {})

            # Boost weeks that cover high-interest skills
            for phase in roadmap.get("phases", []):
                for wt in phase.get("weekly_tasks", []):
                    topic = wt.get("topic", "").lower()
                    interest = max(
                        (skill_interest.get(s, 0) for s in skill_interest if s in topic),
                        default=0,
                    )
                    wt["priority_boost"] = round(interest, 3)

            self.memory.set("roadmap", roadmap, self.name)
            return roadmap

        return {"error": f"Unknown action: {action}"}


class AdvisorAgent(BaseAgent):
    name = "AdvisorAgent"

    def run(self, task: Dict) -> Dict:
        action = task.get("action", "advise")
        resume = self.memory.get("resume_text", "")
        role   = task.get("target_role", self.memory.get("target_role", "Software Engineer"))

        if action == "advise":
            from backend.services.career_advisor import career_advisor
            matches = self.memory.get("job_matches", [])
            advice  = career_advisor.generate_career_advice(
                resume_text=resume,
                target_role=role,
                job_matches=matches,
            )
            self.memory.set("career_advice", advice, self.name)
            return advice

        if action == "synthesise":
            """
            Pull together outputs from ALL other agents and produce a
            unified 'next steps' brief — the thing that makes this feel
            like an agentic system rather than separate endpoints.
            """
            ats      = self.memory.get("ats_score",        {})
            matches  = self.memory.get("ranked_matches",   self.memory.get("job_matches", []))
            roadmap  = self.memory.get("roadmap",          {})
            advice   = self.memory.get("career_advice",    {})
            gaps     = self.memory.get("skill_gaps",       [])
            insights = self.memory.get("market_insights",  {})

            # Build a rich cross-agent context for the synthesising prompt
            context = f"""
ATS Score       : {ats.get('overall_score', 'N/A')}/100 — {ats.get('ats_verdict', '')}
Top Job Match   : {matches[0]['title'] if matches else 'No matches yet'} ({matches[0].get('match_score', '?')}% match)
Skill Gaps      : {', '.join(gaps[:5]) if gaps else 'None identified'}
Market Insights : {str(insights.get('analysis', ''))[:300]}
Action Plan     : {'; '.join(advice.get('action_plan', [])[:3])}
Roadmap Summary : {roadmap.get('summary', 'Not generated yet')}
""".strip()

            prompt = f"""You are a senior career strategist. 
Based on the following cross-functional analysis, write a crisp executive summary 
(5–7 bullet points) telling the candidate exactly what to do THIS WEEK to maximise 
their job search success.

CONTEXT:
{context}

Format: bullet points. Be direct. Prioritise by highest impact.
"""
            synthesis = self._call_llm(prompt, max_tokens=500)
            result = {
                "synthesis":   synthesis,
                "agents_used": self.memory.keys(),
                "trace":       self.memory.trace()[-10:],
            }
            self.memory.set("synthesis", result, self.name)
            return result

        return {"error": f"Unknown action: {action}"}


# ── Orchestrator ───────────────────────────────────────────────────────────────

AGENT_REGISTRY: Dict[str, type] = {
    "ResumeAgent":   ResumeAgent,
    "JobAgent":      JobAgent,
    "InterviewAgent":InterviewAgent,
    "RoadmapAgent":  RoadmapAgent,
    "AdvisorAgent":  AdvisorAgent,
}


class AgentOrchestrator:
    """
    Top-level controller — upgraded with:
      • Uncertainty validation on every agent output
      • LTR re-ranking after job matching
      • Debate-based synthesis for high-stakes recommendations
      • Cross-agent consistency check at end of full_analysis
      • ReAct loop: Plan → Act → Reflect → Replan
    """

    GOAL_PLANS: Dict[str, List[Dict]] = {
        "full_analysis": [
            {"agent": "ResumeAgent",   "action": "ats_score"},
            {"agent": "ResumeAgent",   "action": "extract_skills"},
            {"agent": "ResumeAgent",   "action": "parse_gaps"},
            {"agent": "JobAgent",      "action": "match"},
            {"agent": "JobAgent",      "action": "rank_with_feedback"},
            {"agent": "JobAgent",      "action": "market_insights"},
            {"agent": "RoadmapAgent",  "action": "generate"},
            {"agent": "AdvisorAgent",  "action": "advise"},
            {"agent": "AdvisorAgent",  "action": "debate_synthesise"},  # upgraded
        ],
        "quick_match": [
            {"agent": "ResumeAgent",   "action": "extract_skills"},
            {"agent": "JobAgent",      "action": "match"},
            {"agent": "JobAgent",      "action": "ltr_rank"},           # upgraded
        ],
        "interview_prep": [
            {"agent": "ResumeAgent",   "action": "extract_skills"},
            {"agent": "ResumeAgent",   "action": "parse_gaps"},
            {"agent": "InterviewAgent","action": "generate_questions"},
        ],
        "roadmap_only": [
            {"agent": "ResumeAgent",   "action": "extract_skills"},
            {"agent": "ResumeAgent",   "action": "parse_gaps"},
            {"agent": "RoadmapAgent",  "action": "generate"},
            {"agent": "RoadmapAgent",  "action": "suggest_projects"},
            {"agent": "RoadmapAgent",  "action": "refine_with_feedback"},
        ],
    }

    def __init__(self) -> None:
        self.memory = AgentMemory()
        self._agents: Dict[str, BaseAgent] = {
            name: cls(self.memory)
            for name, cls in AGENT_REGISTRY.items()
        }
        # Wire in new systems
        try:
            from backend.services.uncertainty_handler import get_uncertainty_handler
            self._uh = get_uncertainty_handler()
        except Exception:
            self._uh = None

        try:
            from backend.services.learning_to_rank import get_ltr_engine
            self._ltr = get_ltr_engine()
        except Exception:
            self._ltr = None

        try:
            from backend.services.agent_debate import get_debate_orchestrator
            self._debate = get_debate_orchestrator()
        except Exception:
            self._debate = None

    def load_resume(self, resume_text: str, target_role: str = "Software Engineer") -> None:
        self.memory.set("resume_text", resume_text, "Orchestrator")
        self.memory.set("target_role", target_role, "Orchestrator")

    # ── Validation helpers ─────────────────────────────────────────────────────

    def _validate_output(self, step_key: str, output: Dict) -> Optional[Dict]:
        """
        Run uncertainty checks on agent outputs.
        Returns a confidence report dict (or None if uh unavailable).
        """
        if not self._uh:
            return None
        try:
            if "ats_score" in step_key:
                _, rpt = self._uh.wrap_ats(output)
            elif "match" in step_key:
                _, rpt = self._uh.wrap_matches(output if isinstance(output, list) else [])
            elif "advise" in step_key:
                _, rpt = self._uh.wrap_advice(output)
            elif "roadmap" in step_key or "generate" in step_key:
                _, rpt = self._uh.wrap_roadmap(output)
            else:
                return None
            return rpt.to_dict()
        except Exception as e:
            logger.debug(f"Validation skipped for {step_key}: {e}")
            return None

    # ── LTR re-ranking ─────────────────────────────────────────────────────────

    def _ltr_rerank(self, user_id: str) -> List[Dict]:
        """Re-rank job matches using the learned ranking model."""
        matches = self.memory.get("job_matches", [])
        if not matches or not self._ltr or not user_id:
            return matches
        try:
            from backend.services.feedback_engine import get_feedback_engine
            profile = get_feedback_engine().get_profile(user_id)
            ranked  = self._ltr.rank(user_id, matches, profile)
            self.memory.set("ltr_ranked_matches", ranked, "Orchestrator.LTR")
            logger.info(f"[LTR] Re-ranked {len(ranked)} jobs for user={user_id}")
            return ranked
        except Exception as e:
            logger.warning(f"LTR rerank failed: {e}")
            return matches

    # ── Debate synthesis ───────────────────────────────────────────────────────

    def _debate_synthesise(self, user_id: str) -> Dict:
        """
        Run the full debate loop over the cross-agent context
        and return a consensus recommendation.
        """
        if not self._debate:
            # Fall back to simple synthesis
            return self.memory.get("synthesis", {})

        context = {
            "ats_score":      self.memory.get("ats_score", {}),
            "job_matches":    self.memory.get("ltr_ranked_matches",
                              self.memory.get("job_matches", []))[:3],
            "skill_gaps":     self.memory.get("skill_gaps", []),
            "market_insights": str(self.memory.get("market_insights", {})
                                   .get("analysis", ""))[:400],
            "roadmap_summary": self.memory.get("roadmap", {}).get("summary", ""),
            "career_advice":   self.memory.get("career_advice", {}),
        }
        try:
            result = self._debate.run_debate(
                topic="What should this candidate do this week to maximise job search success?",
                context=context,
                max_rounds=2,
            )
            debate_dict = self._debate.to_dict(result)
            self.memory.set("debate_result", debate_dict, "Orchestrator.Debate")
            # Combine debate final answer with the trace
            synthesis = {
                **result.final_answer,
                "consensus_score": result.consensus_score,
                "debate_rounds":   result.rounds,
                "agents_used":     list(self.memory.keys()),
            }
            self.memory.set("synthesis", synthesis, "Orchestrator.Debate")
            return synthesis
        except Exception as e:
            logger.error(f"Debate synthesis failed: {e}")
            return self.memory.get("career_advice", {})

    # ── Main execution loop ────────────────────────────────────────────────────

    def run_goal(
        self,
        goal: str,
        user_id: str = "",
        extra_context: Optional[Dict] = None,
        stop_on_error: bool = False,
    ) -> Dict:
        plan = self.GOAL_PLANS.get(goal)
        if not plan:
            return {"error": f"Unknown goal '{goal}'. Valid: {list(self.GOAL_PLANS)}"}

        if user_id:
            self.memory.set("user_id", user_id, "Orchestrator")

        results:     Dict[str, Any] = {}
        errors:      List[str]      = []
        confidence:  Dict[str, Any] = {}

        for step in plan:
            agent_name = step["agent"]
            action     = step["action"]
            step_key   = f"{agent_name}.{action}"

            # ── Intercept upgraded actions ─────────────────────────────────
            if action == "debate_synthesise":
                output = self._debate_synthesise(user_id)
                results[step_key] = output
                continue

            if action == "ltr_rank":
                output = {"ltr_ranked_matches": self._ltr_rerank(user_id)}
                results[step_key] = output
                continue

            agent = self._agents.get(agent_name)
            if not agent:
                errors.append(f"Agent '{agent_name}' not found")
                continue

            task = {**step, "user_id": user_id, **(extra_context or {})}
            logger.info(f"[Orchestrator] Running {step_key}")

            try:
                output = agent.run(task)
                results[step_key] = output

                # ── Uncertainty validation ─────────────────────────────────
                rpt = self._validate_output(step_key, output)
                if rpt:
                    confidence[step_key] = rpt
                    if rpt.get("should_retry") and not stop_on_error:
                        logger.warning(
                            f"[Orchestrator] Low confidence on {step_key} "
                            f"({rpt['confidence_score']:.2f}) — retrying once"
                        )
                        output = agent.run({**task, "_retry": True,
                                            "_issues": rpt.get("issues", [])})
                        results[step_key] = output

                # ── LTR re-rank after job matching ─────────────────────────
                if action == "match" and user_id and self._ltr:
                    self._ltr_rerank(user_id)

                if "error" in output:
                    errors.append(f"{step_key}: {output['error']}")
                    if stop_on_error:
                        break

            except Exception as exc:
                err = f"{step_key} raised {type(exc).__name__}: {exc}"
                logger.error(err)
                errors.append(err)
                if stop_on_error:
                    break

        # ── Cross-agent consistency check ──────────────────────────────────
        consistency = {}
        if self._uh:
            try:
                consistency = self._uh.check_consistency(self.memory.snapshot())
            except Exception as e:
                logger.debug(f"Consistency check failed: {e}")

        return {
            "goal":            goal,
            "results":         results,
            "errors":          errors,
            "confidence":      confidence,
            "consistency":     consistency,
            "memory_snapshot": self.memory.snapshot(),
            "trace":           self.memory.trace(),
        }

    def run_task(self, agent_name: str, action: str, **kwargs) -> Dict:
        agent = self._agents.get(agent_name)
        if not agent:
            return {"error": f"Agent '{agent_name}' not registered"}
        return agent.run({"action": action, **kwargs})

    def plan_from_intent(self, user_intent: str, user_id: str = "") -> Dict:
        """LLM-planned dynamic task decomposition (ReAct planning step)."""
        agents_desc = "\n".join(
            f"- {name}: actions = {list(AGENT_REGISTRY.keys())}"
            for name in AGENT_REGISTRY
        )
        prompt = f"""You are a planning AI that decomposes a job-seeker's request into
agent task steps. Available agents and their actions:
{agents_desc}

User request: "{user_intent}"

Return ONLY a JSON array of steps, e.g.:
[
  {{"agent": "ResumeAgent", "action": "ats_score"}},
  {{"agent": "JobAgent",    "action": "match"}}
]
Only include steps that are directly relevant. Max 6 steps."""

        try:
            raw = llm_call_sync(
                system="You are an expert AI assistant. Respond clearly and concisely.",
                user=prompt,
                temp=0.2,
                max_tokens=400,
            )
            raw  = re.sub(r"^```json\s*", "", raw)
            raw  = re.sub(r"\s*```$",     "", raw)
            plan = json.loads(raw)

            results: Dict[str, Any] = {}
            if user_id:
                self.memory.set("user_id", user_id, "Orchestrator")
            for step in plan:
                agent_name = step.get("agent", "")
                action     = step.get("action", "")
                agent      = self._agents.get(agent_name)
                if not agent:
                    continue
                key            = f"{agent_name}.{action}"
                results[key]   = agent.run({"action": action, "user_id": user_id})

            return {"intent": user_intent, "plan": plan, "results": results}
        except Exception as e:
            logger.error(f"Planning error: {e}")
            return {"error": str(e), "intent": user_intent}


# ── Singleton factory ──────────────────────────────────────────────────────────

def get_orchestrator() -> AgentOrchestrator:
    """Return a fresh orchestrator (each session gets its own memory)."""
    return AgentOrchestrator()