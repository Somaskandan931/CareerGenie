"""
backend/services/vector_store.py
==================================
ChromaDB-backed vector store for job listings.

Fixes in this version
---------------------
FIX-1  TF-IDF dimension mismatch
       get_stats() called _get_embeddings(["software"]) before any jobs were
       indexed. fit_transform(["software"]) produces a 1-dim vector (only
       1 non-stop-word), but the ChromaDB collection expected 384 dims from
       a previous SentenceTransformer run → crash logged on every startup.
       Now: skip freshness query when TF-IDF isn't fitted; pad all TF-IDF
       vectors to self._dimension so dim is always consistent.

FIX-2  Stale collection auto-reset
       When a query hits a dim-mismatch error (stale collection from a
       different embedding model), the store now clears itself and returns
       empty so the next match request re-indexes cleanly.

FIX-3  ChromaDB posthog telemetry errors
       posthog 7.x broke the capture() API that chromadb 0.6 uses.
       Suppress at both the env-var and the module level so startup logs
       are clean.

FIX-4  Startup speed
       _ensure_embedder() is no longer triggered during get_stats() when
       the store hasn't been queried yet; saves ~5-20 s on cold starts.
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict
import logging
import os
from pathlib import Path
from datetime import datetime
import numpy as np

# ── Kill ChromaDB telemetry before the posthog module is imported ─────────────
os.environ["ANONYMIZED_TELEMETRY"]   = "False"
os.environ["CHROMA_TELEMETRY"]       = "False"
os.environ["POSTHOG_DISABLED"]       = "true"
os.environ["DISABLE_TELEMETRY"]      = "true"

# Monkey-patch posthog if already loaded (chromadb imports it at module level)
try:
    import posthog as _ph
    _ph.disabled = True
    _original_capture = getattr(_ph, "capture", None)
    if _original_capture:
        _ph.capture = lambda *a, **kw: None  # silence broken API
except Exception:
    pass

from backend.core.config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self):
        """Initialize ChromaDB with lazy embedding loading."""
        persist_dir = Path(settings.CHROMA_PERSIST_DIR)
        persist_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initializing ChromaDB at: {persist_dir}")

        self.client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
                is_persistent=True,
            ),
        )

        self.collection = self.client.get_or_create_collection(
            name="job_listings",
            metadata={"description": "Job listings for RAG matching"},
        )

        # Lazy-loaded embedder
        self.embedder = None
        self._dimension = 384          # target vector length
        self._embedder_initialized = False
        self._use_tfidf = True         # TF-IDF on Render (memory-efficient)
        self._tfidf_fitted = False     # True after first fit_transform on a real corpus
        self._tfidf_corpus: List[str] = []

        logger.info(f"Vector store initialized. Current jobs: {self.collection.count()}")

    # ── Embedder lifecycle ────────────────────────────────────────────────────

    def _ensure_embedder(self):
        """Load embedding model only when first needed (prevents OOM at startup)."""
        if not self._embedder_initialized:
            logger.info("Lazy-loading embedding model...")
            self.embedder = self._init_embedder()
            self._embedder_initialized = True

    def _init_embedder(self):
        is_render = os.environ.get("RENDER", "").lower() == "true"

        if is_render or self._use_tfidf:
            logger.warning("Using lightweight TF-IDF embeddings (Render/constrained mode)")
            from sklearn.feature_extraction.text import TfidfVectorizer
            return TfidfVectorizer(
                max_features=self._dimension,
                stop_words="english",
                lowercase=True,
                strip_accents="unicode",
            )

        try:
            from backend.services.ollama_service import get_ollama_service
            ollama_svc = get_ollama_service()
            if ollama_svc.available:
                logger.info(f"Using Ollama for embeddings ({ollama_svc.embedding_model})")
                self._use_tfidf = False
                return ollama_svc
        except Exception as e:
            logger.info(f"Ollama skipped ({e})")

        try:
            from sentence_transformers import SentenceTransformer
            model_name = getattr(settings, "EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            logger.info(f"Loading SentenceTransformer: {model_name}")
            self._use_tfidf = False
            return SentenceTransformer(model_name)
        except Exception as e:
            logger.error(f"SentenceTransformer failed ({e}); falling back to TF-IDF")
            from sklearn.feature_extraction.text import TfidfVectorizer
            return TfidfVectorizer(
                max_features=self._dimension,
                stop_words="english",
            )

    # ── FIX-1: pad TF-IDF vectors to self._dimension ─────────────────────────

    def _pad(self, vec: list) -> list:
        """Ensure vector is exactly self._dimension long (pad zeros / truncate)."""
        if len(vec) < self._dimension:
            vec = vec + [0.0] * (self._dimension - len(vec))
        return vec[: self._dimension]

    # ── Embedding helpers ─────────────────────────────────────────────────────

    def _get_embedding(self, text: str) -> List[float]:
        """Embed a single text; always returns a list of length self._dimension."""
        return self._get_embeddings([text])[0]

    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of texts.

        TF-IDF path
        -----------
        * First call on a real corpus: fit_transform → pad to self._dimension.
        * Subsequent calls (query time): transform → pad to self._dimension.
        * If transform fails (vocab mismatch), refit on corpus + new texts.

        FIX-1: every vector is padded/truncated to self._dimension so ChromaDB
        never sees a dimension mismatch from a tiny vocabulary.
        """
        self._ensure_embedder()

        try:
            # ── Ollama ────────────────────────────────────────────────────────
            if hasattr(self.embedder, "get_embeddings"):
                embs = self.embedder.get_embeddings(texts)
                if isinstance(embs, np.ndarray):
                    embs = embs.tolist()
                return [self._pad(e) for e in embs]

            if hasattr(self.embedder, "get_embedding"):
                return [self._pad(self.embedder.get_embedding(t)) for t in texts]

            # ── TF-IDF ────────────────────────────────────────────────────────
            if hasattr(self.embedder, "transform"):
                if not self._tfidf_fitted:
                    # FIX-1: fit on provided texts (will be padded if vocab < 384)
                    raw = self.embedder.fit_transform(texts).toarray()
                    self._tfidf_fitted = True
                    self._tfidf_corpus = list(texts)
                    return [self._pad(row.tolist()) for row in raw]
                else:
                    try:
                        raw = self.embedder.transform(texts).toarray()
                        return [self._pad(row.tolist()) for row in raw]
                    except Exception:
                        # Vocab changed — refit on union of old corpus + new texts
                        combined = self._tfidf_corpus + list(texts)
                        self.embedder.fit(combined)
                        self._tfidf_corpus = combined
                        raw = self.embedder.transform(texts).toarray()
                        return [self._pad(row.tolist()) for row in raw]

            # ── SentenceTransformer ───────────────────────────────────────────
            result = self.embedder.encode(texts)
            if isinstance(result, np.ndarray):
                result = result.tolist()
            return [self._pad(r) for r in result]

        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return [[0.0] * self._dimension for _ in texts]

    # ── Public methods ────────────────────────────────────────────────────────

    def index_jobs(self, jobs: List[Dict]) -> int:
        """Index jobs into ChromaDB, auto-resetting on dimension mismatch."""
        if not jobs:
            logger.warning("No jobs to index")
            return 0

        logger.info(f"Indexing {len(jobs)} jobs...")
        documents, metadatas, ids = [], [], []

        for job in jobs:
            job_id = job.get("id")
            if not isinstance(job_id, str) or not job_id.strip():
                logger.error(f"Skipping job with invalid id: {job_id}")
                continue

            title = job.get("title", "")
            description = job.get("description", "")
            if not isinstance(title, str) or not title.strip():
                continue
            if not isinstance(description, str) or not description.strip():
                description = f"We are hiring for {title} position."

            doc_text = f"{title}. {description}"
            documents.append(doc_text)
            metadatas.append({
                "title":           str(title),
                "company":         str(job.get("company",         "Unknown")),
                "location":        str(job.get("location",        "")),
                "apply_link":      str(job.get("apply_link",      "")),
                "employment_type": str(job.get("employment_type", "Full-time")),
                "posted_at":       str(job.get("posted_at",       "")),
                "days_old":        str(job.get("days_old",        "0")),
                "fetched_at":      str(job.get("fetched_at",      datetime.now().isoformat())),
                "indexed_at":      datetime.now().isoformat(),
                "source":          str(job.get("source",          "")),
                "posted_by":       str(job.get("posted_by",       "")),
            })
            ids.append(job_id)

        if not documents:
            logger.warning("No valid jobs after validation")
            return 0

        logger.info("Generating embeddings...")
        try:
            embeddings = self._get_embeddings(documents)
            self.collection.upsert(
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings,
                ids=ids,
            )
            self._count_cache = self.collection.count()
            logger.info(f"Indexed {len(ids)} jobs. Total: {self._count_cache}")
            return len(ids)

        except Exception as e:
            if "dimension" in str(e).lower():
                # FIX-2: stale collection from a different embedding model — reset and retry
                logger.warning(f"Dimension mismatch during index ({e}); resetting collection and retrying")
                self.clear()
                self._tfidf_fitted = False
                self._tfidf_corpus = []
                embeddings = self._get_embeddings(documents)
                self.collection.upsert(
                    documents=documents,
                    metadatas=metadatas,
                    embeddings=embeddings,
                    ids=ids,
                )
                self._count_cache = self.collection.count()
                logger.info(f"Indexed {len(ids)} jobs after reset. Total: {self._count_cache}")
                return len(ids)
            logger.error(f"Index error: {e}")
            raise

    def search(self, query_text: str, top_k: int = 10) -> List[Dict]:
        """Semantic search; auto-resets on dimension mismatch."""
        logger.info(f"Searching top {top_k}...")

        total_jobs = self.collection.count()
        if total_jobs == 0:
            logger.warning("No jobs in vector store")
            return []

        # FIX-4: if TF-IDF not fitted yet, we cannot query reliably — skip
        if self._use_tfidf and not self._tfidf_fitted:
            logger.warning("TF-IDF not fitted yet — skipping search until first index_jobs()")
            return []

        try:
            query_embedding = self._get_embeddings([query_text])
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=min(top_k * 2, total_jobs),
            )

            jobs = []
            if results.get("metadatas") and results["metadatas"]:
                for idx, metadata in enumerate(results["metadatas"][0]):
                    base_distance = (results["distances"][0][idx]
                                     if results.get("distances") else 0.5)
                    days_old = int(metadata.get("days_old", "7"))
                    freshness_boost = 0.1 * max(0, (30 - min(days_old, 30)) / 30)
                    adjusted_distance = max(0, base_distance - freshness_boost)

                    jobs.append({
                        "id":              results["ids"][0][idx],
                        "title":           metadata.get("title",           ""),
                        "company":         metadata.get("company",         ""),
                        "location":        metadata.get("location",        ""),
                        "description":     (results["documents"][0][idx]
                                            if results.get("documents") else ""),
                        "apply_link":      metadata.get("apply_link",      ""),
                        "employment_type": metadata.get("employment_type", "Full-time"),
                        "posted_at":       metadata.get("posted_at",       ""),
                        "source":          metadata.get("source",          ""),
                        "days_old":        int(metadata.get("days_old",    "0")),
                        "fetched_at":      metadata.get("fetched_at",      ""),
                        "distance":        adjusted_distance,
                        "base_distance":   base_distance,
                    })

            jobs.sort(key=lambda x: x["distance"])
            logger.info(f"Found {len(jobs)} matching jobs")
            return jobs[:top_k]

        except Exception as e:
            if "dimension" in str(e).lower():
                # FIX-2: stale embedding mismatch — nuke collection so next
                # index_jobs() rebuilds it with the current embedder.
                logger.warning(f"Dimension mismatch on search ({e}); clearing stale collection")
                self.clear()
                self._tfidf_fitted = False
                self._tfidf_corpus = []
                return []
            logger.error(f"Search error: {e}")
            return []

    def get_stats(self) -> Dict:
        """
        Return vector store stats.

        FIX-1 / FIX-4: skip the freshness ChromaDB query when TF-IDF hasn't
        been fitted yet; avoids the 'dimension 1 ≠ 384' error logged on every
        cold start.
        """
        count_cache = getattr(self, "_count_cache", -1)
        count = count_cache if count_cache >= 0 else self.collection.count()
        self._count_cache = count

        freshness = "unknown"
        avg_days_old = 0

        if count > 0 and not (self._use_tfidf and not self._tfidf_fitted):
            # Only run the query when the embedder is ready to produce valid vectors
            try:
                sample_emb = self._get_embeddings(["software"])
                sample = self.collection.query(
                    query_embeddings=sample_emb,
                    n_results=min(10, count),
                )
                if sample.get("metadatas"):
                    days_list = [int(m.get("days_old", "7"))
                                 for m in sample["metadatas"][0]]
                    if days_list:
                        avg_days_old = sum(days_list) / len(days_list)
                        if avg_days_old <= 3:
                            freshness = "very fresh"
                        elif avg_days_old <= 7:
                            freshness = "fresh"
                        elif avg_days_old <= 14:
                            freshness = "moderate"
                        else:
                            freshness = "stale"
            except Exception as e:
                logger.error(f"Error checking freshness: {e}")

        embedder_info = "TF-IDF" if self._use_tfidf else (
            "Ollama" if hasattr(self.embedder, "available") else "SentenceTransformer"
        )

        return {
            "total_jobs":        count,
            "collection_name":   self.collection.name,
            "persist_directory": settings.CHROMA_PERSIST_DIR,
            "freshness":         freshness,
            "avg_days_old":      round(avg_days_old, 1),
            "embedder":          embedder_info,
        }

    def clear(self):
        """Clear all jobs from the vector store."""
        try:
            self.client.delete_collection("job_listings")
            self.collection = self.client.get_or_create_collection(name="job_listings")
            self._count_cache = 0
            logger.info("Vector store cleared")
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")


# ── Singleton — graceful failure ──────────────────────────────────────────────

vector_store = None

try:
    vector_store = VectorStore()
    logger.info("Vector store singleton created (lazy loading enabled)")
except Exception as e:
    logger.exception(f"VectorStore init failed; starting in degraded mode: {e}")
    try:
        if hasattr(settings, "CHROMA_PERSIST_DIR"):
            sqlite_path = Path(settings.CHROMA_PERSIST_DIR) / "chroma.sqlite3"
            if sqlite_path.exists():
                logger.warning("Deleting stale Chroma sqlite at %s", sqlite_path)
                sqlite_path.unlink()
    except Exception as cleanup_exc:
        logger.warning(f"Chroma cleanup failed: {cleanup_exc}")