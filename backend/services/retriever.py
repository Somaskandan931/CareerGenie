"""
rag/retriever.py
=================
RAG retriever — wraps the existing ChromaDB vector store and adds a structured
context builder so agents receive grounded, relevant context before answering.

What this does:
  1. Retrieves top-k relevant job documents from ChromaDB using the query embedding
  2. Retrieves relevant skill / advice context from a dedicated knowledge collection
  3. Formats retrieved documents into a structured context block that agents
     can paste directly into their prompts

Why it's separate from vector_store.py:
  - vector_store.py is the low-level ChromaDB wrapper (indexing, upserting)
  - retriever.py is the high-level RAG interface (query → formatted context)
  - Keeps concerns separated; retriever can swap backends without touching agents

Integration:
  - Used by the /ask endpoint and the orchestrator before dispatching to proposers
  - The formatted context is stored in AgentMemory under "rag_context"
"""
from __future__ import annotations

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# ── Lazy imports ───────────────────────────────────────────────────────────────
_model      = None
_job_store  = None   # the main vector_store (already has indexed jobs)


def _get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as e:
            logger.warning(f"RAG retriever: SentenceTransformer unavailable — {e}")
    return _model


def _get_job_store():
    global _job_store
    if _job_store is None:
        try:
            from backend.services.vector_store import vector_store
            _job_store = vector_store
        except Exception as e:
            logger.warning(f"RAG retriever: vector_store unavailable — {e}")
    return _job_store


# ── Core retrieval ─────────────────────────────────────────────────────────────

def retrieve_jobs(query: str, top_k: int = 3) -> List[dict]:
    """
    Retrieve the top-k most relevant jobs from the ChromaDB vector store.

    Args:
        query:  The user's query / resume text to embed and search.
        top_k:  Number of results to return.

    Returns:
        List of job dicts {title, company, location, description, distance}.
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

    Args:
        query:  The question / intent to ground with retrieved context.
        top_k:  Number of job documents to retrieve.

    Returns:
        A formatted multi-line string:
            RETRIEVED CONTEXT (top 3 relevant items):
            1. [Job Title] at [Company] — [Location]
               [First 200 chars of description]
            ...
        Returns empty string if no documents are found.
    """
    jobs = retrieve_jobs(query, top_k=top_k)
    if not jobs:
        return ""

    lines = [f"RETRIEVED CONTEXT (top {len(jobs)} relevant job posting(s)):"]
    for i, job in enumerate(jobs, 1):
        title   = job.get("title",       "Unknown Title")
        company = job.get("company",     "Unknown Company")
        loc     = job.get("location",    "")
        desc    = job.get("description", "")[:200]
        lines.append(f"\n{i}. {title} at {company}" + (f" — {loc}" if loc else ""))
        if desc:
            lines.append(f"   {desc}…")

    return "\n".join(lines)


def retrieve(query: str) -> str:
    """Alias for retrieve_context — matches the interface in the god-mode doc."""
    return retrieve_context(query)
