"""
rag/retriever.py
=================
RAG retriever — wraps the existing ChromaDB vector store and adds a structured
context builder so agents receive grounded, relevant context before answering.
"""
from __future__ import annotations

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# ── Lazy imports ───────────────────────────────────────────────────────────────
_model = None
_job_store = None


def _get_model():
    global _model
    if _model is not None:
        return _model

    # Try Ollama first
    try:
        from backend.services.ollama_service import get_ollama_service
        _model = get_ollama_service()
        if _model and _model.available:
            logger.info("RAG retriever: Ollama embedder loaded")
            return _model
    except Exception as e:
        logger.warning(f"RAG retriever: Ollama unavailable ({e})")

    # Fallback to SentenceTransformer
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("RAG retriever: SentenceTransformer loaded")
        return _model
    except Exception as e:
        logger.warning(f"RAG retriever: SentenceTransformer unavailable — {e}")

    return None


def _get_job_store():
    global _job_store
    if _job_store is None:
        try:
            from backend.services.vector_store import vector_store
            _job_store = vector_store
        except Exception as e:
            logger.warning(f"RAG retriever: vector_store unavailable — {e}")
    return _job_store


def retrieve_jobs(query: str, top_k: int = 3) -> List[dict]:
    """
    Retrieve the top-k most relevant jobs from the ChromaDB vector store.
    """
    store = _get_job_store()
    if store is None:
        return []

    try:
        results = store.search(query, top_k=top_k)
        return results or []
    except Exception as e:
        logger.error(f"retrieve_jobs failed: {e}")
        return []


def retrieve_context(query: str, top_k: int = 3) -> str:
    """
    Main RAG entry point — retrieve relevant jobs and format into a structured
    context block ready to be injected into an agent prompt.
    """
    jobs = retrieve_jobs(query, top_k=top_k)
    if not jobs:
        return ""

    lines = [f"RETRIEVED CONTEXT (top {len(jobs)} relevant job posting(s)):"]
    for i, job in enumerate(jobs, 1):
        title = job.get("title", "Unknown Title")
        company = job.get("company", "Unknown Company")
        loc = job.get("location", "")
        desc = job.get("description", "")[:200]
        lines.append(f"\n{i}. {title} at {company}" + (f" — {loc}" if loc else ""))
        if desc:
            lines.append(f"   {desc}…")

    return "\n".join(lines)


def retrieve(query: str) -> str:
    """Alias for retrieve_context."""
    return retrieve_context(query)