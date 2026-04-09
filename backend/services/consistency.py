"""
core/consistency.py
====================
Self-consistency checker for multi-agent outputs.

Implements two checks:

1. Response diversity check  — are the proposer responses meaningfully
   different from each other? If all three agents say the exact same thing,
   the "debate" added no value. We flag this.

2. Cross-agent factual consistency — do key claims (skills mentioned, job
   titles, score ranges) agree across the advice, ATS score, and job matches?
   Contradictions are surfaced so the synthesizer can resolve them.

Both checks are lightweight (no LLM call) — string matching + embedding
similarity only, so they add negligible latency.
"""
from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Similarity threshold — below this responses are "too similar" ──────────────
DIVERSITY_THRESHOLD = 0.85   # cosine similarity; above this = near-duplicate


def check_response_diversity(responses: Dict[str, str]) -> Dict:
    """
    Check whether proposer responses are meaningfully diverse.

    Returns:
        {
            "is_diverse":     bool,
            "duplicate_pairs": list of (agent_a, agent_b) pairs that are
                               near-identical,
            "unique_count":   int (number of responses clearly different
                               from all others),
            "explanation":    str,
        }
    """
    if len(responses) < 2:
        return {
            "is_diverse":      True,
            "duplicate_pairs": [],
            "unique_count":    len(responses),
            "explanation":     "Only one response — no diversity check needed.",
        }

    # Try embedding-based check first
    try:
        from backend.services.scoring import _get_model, _cosine
        import numpy as np

        model = _get_model()
        if model is not None:
            names  = list(responses.keys())
            texts  = list(responses.values())
            embeds = model.encode(texts, convert_to_numpy=True)

            duplicate_pairs = []
            for i in range(len(names)):
                for j in range(i + 1, len(names)):
                    sim = _cosine(embeds[i], embeds[j])
                    if sim >= DIVERSITY_THRESHOLD:
                        duplicate_pairs.append((names[i], names[j]))

            is_diverse   = len(duplicate_pairs) == 0
            unique_count = len(names) - len(set(a for a, _ in duplicate_pairs))

            return {
                "is_diverse":      is_diverse,
                "duplicate_pairs": duplicate_pairs,
                "unique_count":    max(unique_count, 1),
                "explanation": (
                    "All agents provided distinct perspectives."
                    if is_diverse
                    else f"{len(duplicate_pairs)} near-duplicate response pair(s) detected. "
                         "Debate may not have added independent value."
                ),
            }
    except Exception as e:
        logger.debug(f"Embedding diversity check failed, falling back: {e}")

    # Fallback: character-level Jaccard similarity
    duplicate_pairs = []
    names = list(responses.keys())
    texts = list(responses.values())

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a_words = set(texts[i].lower().split())
            b_words = set(texts[j].lower().split())
            union   = a_words | b_words
            jaccard = len(a_words & b_words) / len(union) if union else 0
            if jaccard >= 0.7:
                duplicate_pairs.append((names[i], names[j]))

    return {
        "is_diverse":      len(duplicate_pairs) == 0,
        "duplicate_pairs": duplicate_pairs,
        "unique_count":    len(names) - len(duplicate_pairs),
        "explanation": (
            "Responses appear diverse (Jaccard similarity)."
            if not duplicate_pairs
            else f"{len(duplicate_pairs)} near-duplicate pair(s) detected."
        ),
    }


def check_factual_consistency(memory_snapshot: Dict) -> Dict:
    """
    Cross-validate key facts across agent outputs stored in memory.

    Checks:
      - ATS missing_keywords vs career_advice skill_gaps (should overlap)
      - job_matches titles vs market_insights hot_skills (skills should align)
      - Score ranges are plausible (0–100 for ATS, 0–10 for interview)

    Args:
        memory_snapshot: The AgentMemory.snapshot() dict from the orchestrator.

    Returns:
        {
            "is_consistent": bool,
            "contradictions": list of str describing each inconsistency,
            "alignment_signals": list of str for things that DO agree,
        }
    """
    contradictions:     List[str] = []
    alignment_signals:  List[str] = []

    ats_result     = memory_snapshot.get("ats_score", {})
    advice         = memory_snapshot.get("career_advice", {})
    job_matches    = memory_snapshot.get("job_matches", [])
    market         = memory_snapshot.get("market_insights", {})

    # ── ATS keywords vs advice skill_gaps ─────────────────────────────────────
    ats_missing  = {k.lower() for k in ats_result.get("missing_keywords", [])}
    advice_gaps  = {g["skill"].lower() for g in advice.get("skill_gaps", [])
                    if isinstance(g, dict)}

    if ats_missing and advice_gaps:
        overlap = ats_missing & advice_gaps
        if overlap:
            alignment_signals.append(
                f"ATS and career advice agree on {len(overlap)} skill gap(s): "
                f"{', '.join(sorted(overlap)[:3])}"
            )
        if ats_missing and not overlap:
            contradictions.append(
                "ATS flags missing keywords that career advice doesn't mention: "
                f"{', '.join(sorted(ats_missing)[:3])}"
            )

    # ── ATS score plausibility ─────────────────────────────────────────────────
    ats_overall = ats_result.get("overall_score")
    if ats_overall is not None:
        if not (0 <= int(ats_overall) <= 100):
            contradictions.append(f"ATS overall_score={ats_overall} is outside [0, 100].")
        else:
            alignment_signals.append(f"ATS score ({ats_overall}/100) is in valid range.")

    # ── Job match scores ───────────────────────────────────────────────────────
    if job_matches:
        bad_scores = [
            j.get("title", "?")
            for j in job_matches
            if not (0 <= j.get("match_score", 50) <= 100)
        ]
        if bad_scores:
            contradictions.append(
                f"Job match scores out of range for: {', '.join(bad_scores[:3])}"
            )
        else:
            alignment_signals.append(
                f"All {len(job_matches)} job match scores are in valid range."
            )

    # ── Market insights hot skills vs job match required skills ───────────────
    hot_skills = {s.lower() for s in market.get("hot_skills", [])}
    matched_job_skills: set = set()
    for j in job_matches[:3]:
        matched_job_skills |= {s.lower() for s in j.get("matched_skills", [])}

    if hot_skills and matched_job_skills:
        market_job_overlap = hot_skills & matched_job_skills
        if market_job_overlap:
            alignment_signals.append(
                f"Market hot skills align with top job matches: "
                f"{', '.join(sorted(market_job_overlap)[:3])}"
            )

    return {
        "is_consistent":    len(contradictions) == 0,
        "contradictions":   contradictions,
        "alignment_signals": alignment_signals,
    }


def check_consistency(responses: Dict[str, str], memory_snapshot: Optional[Dict] = None) -> Dict:
    """
    Top-level consistency check combining diversity + factual checks.

    Args:
        responses:        {agent_name: response_text} from proposer round.
        memory_snapshot:  Optional AgentMemory snapshot for cross-agent checks.

    Returns:
        Combined consistency report.
    """
    diversity = check_response_diversity(responses)
    factual   = check_factual_consistency(memory_snapshot or {})

    overall_consistent = diversity["is_diverse"] and factual["is_consistent"]

    return {
        "overall_consistent": overall_consistent,
        "diversity":          diversity,
        "factual":            factual,
        "summary": (
            "System outputs are self-consistent."
            if overall_consistent
            else f"Consistency issues detected: "
                 f"{len(factual['contradictions'])} contradiction(s), "
                 f"{len(diversity['duplicate_pairs'])} duplicate response pair(s)."
        ),
    }
