from __future__ import annotations
"""
Agent Debate System
====================
Addresses the critique:
  ❌ "Agents don't disagree"
  ❌ "No debate / critique loop"
  ❌ "No self-reflection"
  ❌ "No tool retry logic"
  ❌ "You only have: Plan → Execute"

What we implement (Plan → Act → Reflect → Replan loop):

  1. ProposerAgent    — generates N candidate plans / recommendations
  2. CritiqueAgent    — attacks each proposal, identifies weaknesses and
                        failure modes, assigns a confidence score
  3. SynthesisAgent   — reads all proposals + critiques, selects or merges
                        the best elements into a final recommendation
  4. ReflectionLayer  — after execution, each agent reflects on its own
                        output quality and flags low-confidence results
  5. RetryController  — if confidence < threshold, automatically replans
                        with the critique as additional context

This is the architecture pattern used in:
  - Constitutional AI (Anthropic)
  - Self-Refine (Madaan et al., 2023)
  - LLM-Debate (Du et al., 2023)

We implement it with Groq as the underlying model, no extra frameworks.
"""
import google.genai as genai

import json
import logging
import re
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

from backend.config import settings

_genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
MIN_CONFIDENCE      = 0.6    # below this, trigger retry
MAX_DEBATE_ROUNDS   = 3      # maximum propose → critique → replan cycles
N_PROPOSALS         = 3      # number of distinct proposals per debate round


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class Proposal:
    agent_id:    str
    content:     Dict
    reasoning:   str
    confidence:  float         # 0-1 self-assessed
    round_num:   int = 0

@dataclass
class Critique:
    critic_id:   str
    target_id:   str           # agent_id of proposal being critiqued
    weaknesses:  List[str]
    strengths:   List[str]
    confidence:  float         # critic's confidence in target proposal
    suggested_fix: str

@dataclass
class DebateResult:
    topic:           str
    proposals:       List[Proposal]
    critiques:       List[Critique]
    final_answer:    Dict
    rounds:          int
    consensus_score: float     # 0-1, how much agents agreed
    trace:           List[Dict] = field(default_factory=list)


# ── Base debate agent ──────────────────────────────────────────────────────────

class DebateAgent:
    def __init__(self, agent_id: str, persona: str) -> None:
        self.agent_id = agent_id
        self.persona  = persona

    def _call(self, prompt: str, max_tokens: int = 800, temp: float = 0.7) -> str:
        response = _genai_client.models.generate_content(
            model=settings.GEMINI_SMART_MODEL,
            config=genai.types.GenerateContentConfig(
                system_instruction=self.persona,
                temperature=temp,
                max_output_tokens=max_tokens,
            ),
            contents=prompt,
        )
        return response.text.strip()

    def _parse_json(self, raw: str) -> Any:
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"^```\s*",     "", raw)
        raw = re.sub(r"\s*```$",     "", raw)
        # Find first JSON object or array
        m = re.search(r'(\{.*\}|\[.*\])', raw, re.DOTALL)
        if m:
            return json.loads(m.group(1))
        return json.loads(raw)


# ── Proposer agents (different perspectives) ──────────────────────────────────

class OptimistProposer(DebateAgent):
    """Focuses on opportunities and best-case outcomes."""
    def __init__(self):
        super().__init__(
            "optimist",
            "You are an enthusiastic career strategist. You identify the strongest "
            "opportunities and build ambitious but achievable plans. You highlight "
            "what the candidate does well and how to leverage those strengths."
        )

    def propose(self, topic: str, context: Dict, critique_feedback: str = "") -> Proposal:
        prompt = f"""Topic: {topic}

Context:
{json.dumps(context, indent=2)[:1500]}

{"Previous critique to address: " + critique_feedback if critique_feedback else ""}

Generate a career recommendation plan. Return ONLY valid JSON:
{{
  "action_plan": ["<step 1>", "<step 2>", "<step 3>", "<step 4>", "<step 5>"],
  "top_job_recommendation": "<title and why>",
  "key_insight": "<your most important observation>",
  "timeline": "<realistic timeframe>",
  "confidence": <float 0.0-1.0 — how confident you are in this plan>
}}"""
        raw = self._call(prompt, max_tokens=600)
        try:
            data = self._parse_json(raw)
            return Proposal(
                agent_id=self.agent_id,
                content=data,
                reasoning="Opportunity-focused plan maximising candidate strengths",
                confidence=float(data.get("confidence", 0.7)),
            )
        except Exception as e:
            logger.error(f"OptimistProposer parse error: {e}")
            return Proposal(agent_id=self.agent_id, content={}, reasoning="parse error", confidence=0.3)


class RealistProposer(DebateAgent):
    """Focuses on gaps and pragmatic steps."""
    def __init__(self):
        super().__init__(
            "realist",
            "You are a pragmatic career coach. You identify skill gaps, market realities, "
            "and the most efficient path to employment. You are direct about weaknesses "
            "and prioritise high-impact actions over feel-good advice."
        )

    def propose(self, topic: str, context: Dict, critique_feedback: str = "") -> Proposal:
        prompt = f"""Topic: {topic}

Context:
{json.dumps(context, indent=2)[:1500]}

{"Previous critique to address: " + critique_feedback if critique_feedback else ""}

Generate a gap-focused career recommendation. Return ONLY valid JSON:
{{
  "action_plan": ["<step 1>", "<step 2>", "<step 3>", "<step 4>", "<step 5>"],
  "top_job_recommendation": "<title and why>",
  "key_insight": "<your most important observation>",
  "timeline": "<realistic timeframe>",
  "confidence": <float 0.0-1.0>
}}"""
        raw = self._call(prompt, max_tokens=600)
        try:
            data = self._parse_json(raw)
            return Proposal(
                agent_id=self.agent_id,
                content=data,
                reasoning="Gap-analysis driven plan addressing critical weaknesses",
                confidence=float(data.get("confidence", 0.7)),
            )
        except Exception as e:
            logger.error(f"RealistProposer parse error: {e}")
            return Proposal(agent_id=self.agent_id, content={}, reasoning="parse error", confidence=0.3)


class MarketProposer(DebateAgent):
    """Focuses on market demand and trend alignment."""
    def __init__(self):
        super().__init__(
            "market analyst",
            "You are a labour market specialist. You focus on industry trends, "
            "in-demand skills, salary data, and which roles have the best "
            "supply/demand dynamics. You recommend based on market signals, "
            "not just candidate preference."
        )

    def propose(self, topic: str, context: Dict, critique_feedback: str = "") -> Proposal:
        prompt = f"""Topic: {topic}

Context:
{json.dumps(context, indent=2)[:1500]}

{"Previous critique to address: " + critique_feedback if critique_feedback else ""}

Generate a market-aligned career recommendation. Return ONLY valid JSON:
{{
  "action_plan": ["<step 1>", "<step 2>", "<step 3>", "<step 4>", "<step 5>"],
  "top_job_recommendation": "<title and why>",
  "key_insight": "<your most important observation>",
  "timeline": "<realistic timeframe>",
  "confidence": <float 0.0-1.0>
}}"""
        raw = self._call(prompt, max_tokens=600)
        try:
            data = self._parse_json(raw)
            return Proposal(
                agent_id=self.agent_id,
                content=data,
                reasoning="Market-demand driven plan targeting high-opportunity roles",
                confidence=float(data.get("confidence", 0.7)),
            )
        except Exception as e:
            logger.error(f"MarketProposer parse error: {e}")
            return Proposal(agent_id=self.agent_id, content={}, reasoning="parse error", confidence=0.3)


# ── Critic agent ───────────────────────────────────────────────────────────────

class CriticAgent(DebateAgent):
    """Attacks every proposal — finds weaknesses, inconsistencies, blind spots."""
    def __init__(self):
        super().__init__(
            "critic",
            "You are a harsh but fair career advisor who stress-tests career plans. "
            "You identify unrealistic assumptions, missing steps, logical gaps, and "
            "market realities that contradict the plan. You assign a confidence score "
            "to each plan based on how well it would actually work."
        )

    def critique(self, proposal: Proposal, context: Dict) -> Critique:
        prompt = f"""Critique this career plan:

Plan from {proposal.agent_id}:
{json.dumps(proposal.content, indent=2)}

Reasoning: {proposal.reasoning}

Context (resume/market data):
{json.dumps(context, indent=2)[:800]}

Return ONLY valid JSON:
{{
  "weaknesses": ["<weakness 1>", "<weakness 2>", "<weakness 3>"],
  "strengths": ["<strength 1>", "<strength 2>"],
  "confidence": <float 0.0-1.0 — how likely this plan succeeds>,
  "suggested_fix": "<one specific improvement that would most increase success>"
}}"""
        raw = self._call(prompt, max_tokens=500, temp=0.3)
        try:
            data = self._parse_json(raw)
            return Critique(
                critic_id="critic",
                target_id=proposal.agent_id,
                weaknesses=data.get("weaknesses", []),
                strengths=data.get("strengths",  []),
                confidence=float(data.get("confidence", 0.5)),
                suggested_fix=data.get("suggested_fix", ""),
            )
        except Exception as e:
            logger.error(f"CriticAgent parse error: {e}")
            return Critique(
                critic_id="critic", target_id=proposal.agent_id,
                weaknesses=["Unable to evaluate"], strengths=[],
                confidence=0.4, suggested_fix="",
            )


# ── Reflection layer ───────────────────────────────────────────────────────────

class ReflectionLayer:
    """
    After execution, each agent reviews its own output.
    If self-assessed confidence drops below MIN_CONFIDENCE, flags for retry.
    """
    def __init__(self):
        pass

    def reflect(self, agent_name: str, output: Dict, task_description: str) -> Dict:
        prompt = f"""You just produced this output as the {agent_name}:
{json.dumps(output, indent=2)[:1000]}

Task you were solving: {task_description}

Honestly assess your output. Return ONLY valid JSON:
{{
  "confidence": <float 0.0-1.0>,
  "quality_issues": ["<issue if any>"],
  "missing_elements": ["<what's missing>"],
  "should_retry": <true/false>,
  "retry_hint": "<what to do differently if retrying>"
}}"""
        try:
            response = _genai_client.models.generate_content(
                model=settings.GEMINI_SMART_MODEL,
                config=genai.types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=300,
                ),
                contents=prompt,
        )
            raw  = response.text.strip()
            raw  = re.sub(r"^```json\s*", "", raw)
            raw  = re.sub(r"\s*```$",     "", raw)
            data = json.loads(raw)
            data["agent"]      = agent_name
            data["confidence"] = float(data.get("confidence", 0.6))
            return data
        except Exception as e:
            logger.error(f"ReflectionLayer error: {e}")
            return {"agent": agent_name, "confidence": 0.5, "should_retry": False,
                    "quality_issues": [], "missing_elements": [], "retry_hint": ""}


# ── Synthesis agent ────────────────────────────────────────────────────────────

class SynthesisAgent(DebateAgent):
    """
    Reads all proposals and critiques, selects the best elements,
    and produces a final unified recommendation.
    """
    def __init__(self):
        super().__init__(
            "synthesizer",
            "You are a senior career strategist and judge. You read multiple "
            "competing career plans and their critiques, then synthesise the "
            "best elements into a single coherent, balanced recommendation. "
            "You are impartial and evidence-based."
        )

    def synthesise(
        self,
        proposals: List[Proposal],
        critiques:  List[Critique],
        context:    Dict,
        topic:      str,
    ) -> Tuple[Dict, float]:
        """Returns (final_recommendation, consensus_score)."""

        proposals_text = "\n\n".join([
            f"=== {p.agent_id.upper()} PROPOSAL ===\n"
            f"Plan: {json.dumps(p.content, indent=2)}\n"
            f"Self-confidence: {p.confidence}"
            for p in proposals if p.content
        ])

        critiques_text = "\n\n".join([
            f"--- CRITIQUE of {c.target_id} ---\n"
            f"Weaknesses: {'; '.join(c.weaknesses)}\n"
            f"Strengths: {'; '.join(c.strengths)}\n"
            f"Critic confidence: {c.confidence}\n"
            f"Fix: {c.suggested_fix}"
            for c in critiques
        ])

        prompt = f"""Topic: {topic}

PROPOSALS:
{proposals_text}

CRITIQUES:
{critiques_text}

CONTEXT:
{json.dumps(context, indent=2)[:800]}

Synthesise the best plan. Return ONLY valid JSON:
{{
  "action_plan": ["<best step 1>", "<best step 2>", "<best step 3>", "<best step 4>", "<best step 5>"],
  "top_job_recommendation": "<most defensible recommendation>",
  "key_insight": "<the single most important thing for this candidate>",
  "timeline": "<realistic timeframe>",
  "elements_adopted_from": {{
    "optimist": "<what you took from the optimist>",
    "realist": "<what you took from the realist>",
    "market": "<what you took from the market analyst>"
  }},
  "consensus_score": <float 0.0-1.0 — how much did agents agree overall>
}}"""
        raw = self._call(prompt, max_tokens=800, temp=0.2)
        try:
            data           = self._parse_json(raw)
            consensus      = float(data.pop("consensus_score", 0.6))
            return data, consensus
        except Exception as e:
            logger.error(f"SynthesisAgent parse error: {e}")
            # Fallback: take highest-confidence proposal
            best = max(proposals, key=lambda p: p.confidence, default=None)
            return (best.content if best else {}), 0.4


# ── Retry controller ───────────────────────────────────────────────────────────

class RetryController:
    """
    Monitors agent outputs and triggers replanning when confidence is low.
    Implements the Reflect → Replan portion of the ReAct loop.
    """
    def __init__(self, threshold: float = MIN_CONFIDENCE):
        self.threshold  = threshold
        self.reflection = ReflectionLayer()

    def check_and_retry(
        self,
        agent_name: str,
        output: Dict,
        task_description: str,
        retry_fn,           # callable that produces a new output
        max_retries: int = 2,
    ) -> Tuple[Dict, Dict]:
        """
        Check output quality; retry up to max_retries times if needed.
        Returns (final_output, reflection_log).
        """
        reflection_log = []

        for attempt in range(max_retries + 1):
            reflection = self.reflection.reflect(agent_name, output, task_description)
            reflection_log.append({**reflection, "attempt": attempt})

            if not reflection.get("should_retry", False) \
               or reflection["confidence"] >= self.threshold \
               or attempt >= max_retries:
                break

            logger.info(
                f"[RetryController] {agent_name} low confidence "
                f"({reflection['confidence']:.2f}) — retrying (attempt {attempt+1})"
            )
            retry_hint = reflection.get("retry_hint", "")
            output     = retry_fn(hint=retry_hint)

        return output, {
            "attempts":        len(reflection_log),
            "final_confidence": reflection_log[-1]["confidence"] if reflection_log else 0.5,
            "reflections":      reflection_log,
        }


# ── Debate Orchestrator ────────────────────────────────────────────────────────

class DebateOrchestrator:
    """
    Runs the full propose → critique → synthesise → reflect loop.

    Usage:
        orchestrator = DebateOrchestrator()
        result = orchestrator.run_debate(
            topic="What should this candidate do next?",
            context={"resume_skills": [...], "job_matches": [...], "ats_score": {...}}
        )
        print(result.final_answer)
        print(f"Consensus: {result.consensus_score:.2f}")
    """

    def __init__(self):
        self.proposers = [
            OptimistProposer(),
            RealistProposer(),
            MarketProposer(),
        ]
        self.critic    = CriticAgent()
        self.synthesis = SynthesisAgent()
        self.retry_ctl = RetryController()

    def run_debate(
        self,
        topic:    str,
        context:  Dict,
        max_rounds: int = MAX_DEBATE_ROUNDS,
    ) -> DebateResult:
        """
        Full debate loop:
          Round 1: All proposers generate initial plans
          Round 2: Critic attacks each plan
          Round 3: Proposers revise based on critique (if consensus < threshold)
          Final:   Synthesis agent produces unified recommendation
        """
        all_proposals: List[Proposal] = []
        all_critiques: List[Critique] = []
        trace: List[Dict] = []

        feedback_map: Dict[str, str] = {}  # agent_id -> latest critique feedback

        for round_num in range(1, max_rounds + 1):
            trace.append({"round": round_num, "event": "propose_start", "ts": time.time()})

            # ── Propose ────────────────────────────────────────────────────────
            round_proposals = []
            for proposer in self.proposers:
                hint = feedback_map.get(proposer.agent_id, "")
                prop = proposer.propose(topic, context, hint)
                prop.round_num = round_num
                round_proposals.append(prop)
                trace.append({
                    "round":       round_num,
                    "event":       "proposal",
                    "agent":       proposer.agent_id,
                    "confidence":  prop.confidence,
                })

            all_proposals.extend(round_proposals)

            # ── Critique ───────────────────────────────────────────────────────
            round_critiques = []
            for prop in round_proposals:
                if not prop.content:
                    continue
                crit = self.critic.critique(prop, context)
                round_critiques.append(crit)
                feedback_map[prop.agent_id] = (
                    f"Weaknesses found: {'; '.join(crit.weaknesses)}. "
                    f"Suggested fix: {crit.suggested_fix}"
                )
                trace.append({
                    "round":      round_num,
                    "event":      "critique",
                    "target":     prop.agent_id,
                    "confidence": crit.confidence,
                    "weaknesses": len(crit.weaknesses),
                })

            all_critiques.extend(round_critiques)

            # ── Convergence check ──────────────────────────────────────────────
            avg_confidence = (
                sum(c.confidence for c in round_critiques) / len(round_critiques)
                if round_critiques else 0.5
            )
            trace.append({
                "round":          round_num,
                "event":          "convergence_check",
                "avg_confidence": round(avg_confidence, 3),
            })

            # Stop early if critics are satisfied
            if avg_confidence >= 0.75 and round_num > 1:
                logger.info(
                    f"[Debate] Early convergence at round {round_num} "
                    f"(avg critic confidence={avg_confidence:.2f})"
                )
                break

        # ── Synthesise ─────────────────────────────────────────────────────────
        trace.append({"event": "synthesise_start", "ts": time.time()})
        final_answer, consensus = self.synthesis.synthesise(
            all_proposals, all_critiques, context, topic
        )

        # ── Reflect on synthesis ───────────────────────────────────────────────
        final_answer, retry_log = self.retry_ctl.check_and_retry(
            agent_name="synthesizer",
            output=final_answer,
            task_description=topic,
            retry_fn=lambda hint="": self.synthesis.synthesise(
                all_proposals, all_critiques,
                {**context, "retry_hint": hint},
                topic,
            )[0],
        )
        trace.append({"event": "reflection", "log": retry_log})

        return DebateResult(
            topic=topic,
            proposals=all_proposals,
            critiques=all_critiques,
            final_answer=final_answer,
            rounds=round_num,
            consensus_score=consensus,
            trace=trace,
        )

    def quick_critique(self, plan: Dict, context: Dict) -> Dict:
        """
        Lightweight single-round critique of an existing plan.
        Useful for validating advisor output without a full debate.
        """
        prop = Proposal(
            agent_id="external",
            content=plan,
            reasoning="Externally generated plan",
            confidence=0.7,
        )
        crit = self.critic.critique(prop, context)
        return {
            "weaknesses":    crit.weaknesses,
            "strengths":     crit.strengths,
            "confidence":    crit.confidence,
            "suggested_fix": crit.suggested_fix,
        }

    def to_dict(self, result: DebateResult) -> Dict:
        """Serialise a DebateResult for JSON response."""
        return {
            "topic":           result.topic,
            "final_answer":    result.final_answer,
            "rounds":          result.rounds,
            "consensus_score": result.consensus_score,
            "proposals": [
                {
                    "agent_id":   p.agent_id,
                    "content":    p.content,
                    "confidence": p.confidence,
                    "round":      p.round_num,
                }
                for p in result.proposals
            ],
            "critiques": [
                {
                    "target":       c.target_id,
                    "weaknesses":   c.weaknesses,
                    "strengths":    c.strengths,
                    "confidence":   c.confidence,
                    "fix":          c.suggested_fix,
                }
                for c in result.critiques
            ],
            "trace": result.trace,
        }


# ── Singleton ──────────────────────────────────────────────────────────────────
_debate_orchestrator: Optional[DebateOrchestrator] = None


def get_debate_orchestrator() -> DebateOrchestrator:
    global _debate_orchestrator
    if _debate_orchestrator is None:
        _debate_orchestrator = DebateOrchestrator()
    return _debate_orchestrator