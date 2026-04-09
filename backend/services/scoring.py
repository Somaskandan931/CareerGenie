"""
core/scoring.py
================
Scoring and voting engine for the multi-agent debate system.

Implements:
  1. Relevance scoring   — cosine similarity between query embedding and each
                           agent response embedding (how on-topic is the answer?)
  2. Diversity scoring   — penalise responses that are too similar to each other
                           (rewards unique perspectives from different proposers)
  3. Weighted voting     — combines relevance + diversity into a final per-agent
                           weight used by the synthesizer
  4. Winner selection    — pick the highest-scoring proposal as the base answer

Uses the same SentenceTransformer model already loaded by vector_store.py
(all-MiniLM-L6-v2) — no new model is downloaded.

Design note:
  Scoring is synchronous and CPU-bound. It's fast enough (~10ms for 3 proposals)
  that it doesn't need async treatment.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ── Lazy model loading — reuses the same model as vector_store ─────────────────
_model = None

def _get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Scoring: SentenceTransformer loaded")
        except Exception as e:
            logger.warning(f"Scoring: SentenceTransformer unavailable ({e}) — falling back to length heuristic")
    return _model


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denom) if denom > 0 else 0.0


def score_responses(query: str, responses: Dict[str, str]) -> Dict[str, float]:
    """
    Score each agent response against the query using cosine similarity.

    Args:
        query:     The original user query / topic.
        responses: {agent_name: response_text} dict from the proposer round.

    Returns:
        {agent_name: score}  where score ∈ [0, 1].
        Higher = more relevant to the query.
    """
    if not responses:
        return {}

    model = _get_model()

    if model is None:
        # Fallback: score by response length (longer = more detailed = higher score)
        # Normalised to [0, 1]
        lengths = {k: len(v) for k, v in responses.items()}
        max_len = max(lengths.values()) or 1
        return {k: round(v / max_len, 3) for k, v in lengths.items()}

    try:
        texts  = [query] + list(responses.values())
        embeds = model.encode(texts, convert_to_numpy=True)
        q_emb  = embeds[0]
        r_embs = embeds[1:]

        scores = {}
        for i, agent_name in enumerate(responses):
            scores[agent_name] = round(_cosine(q_emb, r_embs[i]), 4)
        return scores

    except Exception as e:
        logger.error(f"score_responses failed: {e}")
        return {k: 0.5 for k in responses}


def diversity_penalty(responses: Dict[str, str]) -> Dict[str, float]:
    """
    Compute a diversity score for each agent — higher means the response is
    more distinct from the others (penalises copy-paste or near-identical outputs).

    Returns:
        {agent_name: diversity_score}  ∈ [0, 1]
        1.0 = maximally different from all others
        0.0 = identical to another response
    """
    if len(responses) < 2:
        return {k: 1.0 for k in responses}

    model = _get_model()
    if model is None:
        return {k: 1.0 for k in responses}

    try:
        names  = list(responses.keys())
        texts  = list(responses.values())
        embeds = model.encode(texts, convert_to_numpy=True)

        diversity: Dict[str, float] = {}
        for i, name in enumerate(names):
            # Average cosine similarity to all OTHER responses
            sims = [
                _cosine(embeds[i], embeds[j])
                for j in range(len(names)) if j != i
            ]
            avg_sim = sum(sims) / len(sims) if sims else 0.0
            diversity[name] = round(1.0 - avg_sim, 4)  # higher = more diverse
        return diversity

    except Exception as e:
        logger.error(f"diversity_penalty failed: {e}")
        return {k: 1.0 for k in responses}


def weighted_vote(
    query: str,
    responses: Dict[str, str],
    relevance_weight: float = 0.7,
    diversity_weight: float = 0.3,
) -> Tuple[Dict[str, float], str]:
    """
    Combine relevance and diversity into a final vote score per agent.
    Returns the combined scores dict and the name of the winning agent.

    Args:
        query:             Original query.
        responses:         {agent_name: response_text}.
        relevance_weight:  Weight given to query relevance (default 0.7).
        diversity_weight:  Weight given to diversity from peers (default 0.3).

    Returns:
        (scores_dict, winner_agent_name)
    """
    rel   = score_responses(query, responses)
    div   = diversity_penalty(responses)

    combined: Dict[str, float] = {}
    for name in responses:
        r = rel.get(name, 0.5)
        d = div.get(name, 1.0)
        combined[name] = round(relevance_weight * r + diversity_weight * d, 4)

    winner = max(combined, key=combined.get) if combined else next(iter(responses), "")
    logger.debug(f"Vote scores: {combined} | winner: {winner}")
    return combined, winner
