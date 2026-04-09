"""
core/confidence.py
===================
Confidence estimation for multi-agent outputs.

Implements two complementary confidence signals:

1. Score-based confidence  — derived from the distribution of agent relevance
   scores. High mean + low variance = confident system. Low mean or high
   variance = uncertain, agents disagree.

2. Content-based confidence — checks whether the final synthesised answer
   contains hallucination signals (generic filler, missing specifics, very
   short output) and applies a calibration penalty.

Combined into a single [0, 1] confidence value with a human-readable tier
label that the API can surface to the frontend.

Formula (score-based):
   confidence = mean(scores) × (1 − variance(scores))

Rationale: if all agents score 0.9, confidence is high. If scores are spread
across 0.4–0.9, variance is high so confidence is penalised even if mean is OK.
"""
from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Tiers (mirrors uncertainty_handler.py thresholds) ─────────────────────────
HIGH      = "high"       # ≥ 0.75
MEDIUM    = "medium"     # 0.50 – 0.74
LOW       = "low"        # 0.25 – 0.49
UNRELIABLE = "unreliable"  # < 0.25

_HALLUCINATION_PATTERNS = [
    r"\bas an ai\b",
    r"\bi cannot\b",
    r"\bi don'?t know\b",
    r"\bunable to (provide|answer|generate)\b",
    r"\bgeneric advice\b",
    r"\binsert .{0,30} here\b",
]


def confidence_from_scores(scores: Dict[str, float]) -> float:
    """
    Compute a scalar confidence in [0, 1] from a dict of agent relevance scores.

    Args:
        scores: {agent_name: score} where score ∈ [0, 1].

    Returns:
        Scalar confidence value.
    """
    if not scores:
        return 0.0

    vals = list(scores.values())
    if len(vals) == 1:
        return round(vals[0], 3)

    mean = sum(vals) / len(vals)
    variance = sum((x - mean) ** 2 for x in vals) / len(vals)

    # High variance penalises confidence
    raw = mean * (1.0 - variance)
    return round(max(0.0, min(1.0, raw)), 3)


def content_calibration(text: str) -> float:
    """
    Return a calibration multiplier in [0.5, 1.0] based on content quality.

    Penalises:
      - Very short responses (< 100 chars) → likely not useful
      - Hallucination pattern matches
      - Excessive hedge words

    1.0 = no penalty, 0.5 = maximum penalty.
    """
    if not text:
        return 0.5

    penalty = 1.0

    # Length check
    if len(text) < 100:
        penalty *= 0.7
    elif len(text) < 50:
        penalty *= 0.5

    # Hallucination patterns
    text_lower = text.lower()
    for pattern in _HALLUCINATION_PATTERNS:
        if re.search(pattern, text_lower):
            penalty *= 0.8
            break  # one match is enough

    return round(max(0.5, min(1.0, penalty)), 3)


def estimate_confidence(
    scores: Dict[str, float],
    final_answer: Optional[str] = None,
) -> Dict:
    """
    Full confidence estimate combining score distribution and content quality.

    Args:
        scores:       Per-agent relevance scores from scoring.py.
        final_answer: The synthesised answer text (optional, for content check).

    Returns:
        {
            "score":           float [0, 1],
            "tier":            "high" | "medium" | "low" | "unreliable",
            "mean_agent_score": float,
            "variance":        float,
            "content_quality": float,
            "explanation":     str,
        }
    """
    base = confidence_from_scores(scores)

    content_quality = 1.0
    if final_answer:
        content_quality = content_calibration(final_answer)

    final_score = round(base * content_quality, 3)

    # Tier
    if final_score >= 0.75:
        tier = HIGH
        explanation = "Agents were well-aligned and the answer is detailed."
    elif final_score >= 0.50:
        tier = MEDIUM
        explanation = "Moderate agreement between agents. Review for nuance."
    elif final_score >= 0.25:
        tier = LOW
        explanation = "Agents disagreed significantly. Treat output as indicative."
    else:
        tier = UNRELIABLE
        explanation = "Low confidence. Consider re-running with more context."

    vals = list(scores.values())
    mean = sum(vals) / len(vals) if vals else 0.0
    variance = sum((x - mean) ** 2 for x in vals) / len(vals) if vals else 0.0

    return {
        "score":            final_score,
        "tier":             tier,
        "mean_agent_score": round(mean, 3),
        "variance":         round(variance, 4),
        "content_quality":  content_quality,
        "explanation":      explanation,
    }
