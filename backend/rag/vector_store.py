import os
import time
import hashlib
from typing import List, Dict

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# ------------------------------------------------------------------
# Persistent ChromaDB configuration (Windows-safe)
# ------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DIR = os.path.join(BASE_DIR, "..", "chroma_data")

client = chromadb.Client(
    Settings(
        persist_directory=CHROMA_DIR,
        anonymized_telemetry=False
    )
)

collection = client.get_or_create_collection(name="career_genie_jobs")

embedder = SentenceTransformer("all-MiniLM-L6-v2")
CACHE_TTL = 86400  # 24 hours


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _job_hash(job: Dict) -> str:
    raw = f"{job.get('title')}{job.get('company')}{job.get('location')}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


# ------------------------------------------------------------------
# Vector indexing
# ------------------------------------------------------------------

def index_jobs(jobs: List[Dict]):
    now = int(time.time())

    documents = []
    metadatas = []
    ids = []

    for job in jobs:
        job_id = _job_hash(job)

        documents.append(f"{job.get('title', '')} {job.get('description', '')}")
        metadatas.append({
            **job,
            "indexed_at": now
        })
        ids.append(job_id)

    if not documents:
        return

    embeddings = embedder.encode(documents).tolist()

    collection.upsert(
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
        ids=ids
    )

    client.persist()


# ------------------------------------------------------------------
# Semantic search
# ------------------------------------------------------------------

def semantic_search(resume_text: str, top_k: int):
    resume_embedding = embedder.encode([resume_text]).tolist()

    results = collection.query(
        query_embeddings=resume_embedding,
        n_results=top_k
    )

    return results.get("metadatas", [[]])[0]


# ------------------------------------------------------------------
# Stats
# ------------------------------------------------------------------

def stats():
    return {
        "total_indexed_jobs": collection.count(),
        "cache_ttl_hours": CACHE_TTL // 3600,
        "storage_path": os.path.abspath(CHROMA_DIR)
    }
