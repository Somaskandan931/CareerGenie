"""
core/scoring.py
================
Scoring and voting engine for the multi-agent debate system.

Implements:
  1. Relevance scoring   — cosine similarity between query embedding and each
                           agent response embedding (how on-topic is the answer?)
  2. Diversity scoring   — penalise responses that are too similar to each other
  3. Weighted voting     — combines relevance + diversity into a final per-agent weight
  4. Winner selection    — pick the highest-scoring proposal as the base answer
"""
from __future__ import annotations

import logging
from typing import Dict, List, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ── Lazy model loading — tries Ollama first, then SentenceTransformer ─────────
_model = None

def _get_model():
    global _model
    if _model is not None:
        return _model

    # Try Ollama first
    try:
        from backend.services.ollama_service import get_ollama_service
        _model = get_ollama_service()
        if _model and _model.available:
            logger.info("Scoring: Ollama embedder loaded")
            return _model
    except Exception as e:
        logger.warning(f"Scoring: Ollama unavailable ({e})")

    # Fallback to SentenceTransformer
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Scoring: SentenceTransformer loaded")
        return _model
    except Exception as e:
        logger.warning(f"Scoring: SentenceTransformer unavailable ({e}) — falling back to length heuristic")

    return None


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denom) if denom > 0 else 0.0


def _get_embedding(model, text: str) -> np.ndarray:
    """Get embedding from either Ollama or SentenceTransformer"""
    if hasattr(model, 'get_embedding'):
        # Ollama
        emb = model.get_embedding(text)
        return np.array(emb)
    else:
        # SentenceTransformer
        return model.encode([text])[0]


def _get_embeddings(model, texts: List[str]) -> np.ndarray:
    """Get embeddings for multiple texts"""
    if hasattr(model, 'get_embeddings'):
        # Ollama
        return model.get_embeddings(texts)
    else:
        # SentenceTransformer
        return model.encode(texts)


def score_responses(query: str, responses: Dict[str, str]) -> Dict[str, float]:
    """
    Score each agent response against the query using cosine similarity.
    """
    if not responses:
        return {}

    model = _get_model()

    if model is None:
        # Fallback: score by response length
        lengths = {k: len(v) for k, v in responses.items()}
        max_len = max(lengths.values()) or 1
        return {k: round(v / max_len, 3) for k, v in lengths.items()}

    try:
        texts = [query] + list(responses.values())

        if hasattr(model, 'get_embeddings'):
            embeds = model.get_embeddings(texts)
            q_emb = embeds[0]
            r_embs = embeds[1:]
        else:
            embeds = model.encode(texts)
            q_emb = embeds[0]
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
    Compute a diversity score for each agent.
    """
    if len(responses) < 2:
        return {k: 1.0 for k in responses}

    model = _get_model()
    if model is None:
        return {k: 1.0 for k in responses}

    try:
        names = list(responses.keys())
        texts = list(responses.values())

        if hasattr(model, 'get_embeddings'):
            embeds = model.get_embeddings(texts)
        else:
            embeds = model.encode(texts)

        diversity: Dict[str, float] = {}
        for i, name in enumerate(names):
            sims = [
                _cosine(embeds[i], embeds[j])
                for j in range(len(names)) if j != i
            ]
            avg_sim = sum(sims) / len(sims) if sims else 0.0
            diversity[name] = round(1.0 - avg_sim, 4)
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
    """
    rel = score_responses(query, responses)
    div = diversity_penalty(responses)

    combined: Dict[str, float] = {}
    for name in responses:
        r = rel.get(name, 0.5)
        d = div.get(name, 1.0)
        combined[name] = round(relevance_weight * r + diversity_weight * d, 4)

    winner = max(combined, key=combined.get) if combined else next(iter(responses), "")
    logger.debug(f"Vote scores: {combined} | winner: {winner}")
    return combined, winner