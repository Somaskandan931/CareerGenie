"""
Ollama Service - Local LLM and Embeddings Provider
Optimized for speed:
  - Persistent requests.Session (connection pooling / keep-alive)
  - Concurrent batch embeddings via ThreadPoolExecutor
  - Streaming chat with configurable timeout
  - Graceful fallback when embedding fails
"""
import logging
import concurrent.futures
import numpy as np
import requests
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# ── Tune these to taste ───────────────────────────────────────────────────────
_EMBED_TIMEOUT   = 15   # seconds per single embedding call
_CHAT_TIMEOUT    = 45   # seconds for full (non-streamed) chat response
_HEALTH_TIMEOUT  = 3    # seconds for availability ping
_EMBED_WORKERS   = 8    # parallel embedding threads (raise for faster CPUs)
# ─────────────────────────────────────────────────────────────────────────────


class OllamaService:
    """Centralised service for Ollama operations using HTTP API directly."""

    def __init__(
        self,
        host: str = "http://localhost:11434",
        embedding_model: str = "all-minilm",  # Use existing model that works with ChromaDB
        llm_model: str = "llama3.2:3b",
    ):
        self.host            = host
        self.embedding_model = embedding_model
        self.llm_model       = llm_model
        self._dimension      = 384  # all-minilm → 384-dim vectors (matches existing ChromaDB)

        # ── Persistent session with keep-alive and reasonable pool size ──────
        self._session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=_EMBED_WORKERS,
            pool_maxsize=_EMBED_WORKERS + 4,
            max_retries=0,          # we handle retries ourselves
        )
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

        self.available = self._check_availability()

        # Check if embedding model is available
        self._embedding_available = self._check_embedding_model()

        if self.available:
            logger.info(
                f"OllamaService ready — embedding={embedding_model}, "
                f"llm={llm_model}, host={host}, embedding_available={self._embedding_available}"
            )
        else:
            logger.warning(f"Ollama not available at {host}. Run 'ollama serve' first.")

    # ── Availability ──────────────────────────────────────────────────────────

    def _check_availability(self) -> bool:
        try:
            r = self._session.get(f"{self.host}/api/tags", timeout=_HEALTH_TIMEOUT)
            if r.status_code == 200:
                names = [m.get("name", "") for m in r.json().get("models", [])]
                logger.info(f"Ollama models: {names}")
                return True
        except Exception as e:
            logger.debug(f"Ollama check failed: {e}")
        return False

    def _check_embedding_model(self) -> bool:
        """Check if the embedding model is available in Ollama."""
        if not self.available:
            return False
        try:
            r = self._session.get(f"{self.host}/api/tags", timeout=_HEALTH_TIMEOUT)
            if r.status_code == 200:
                models = r.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                if any(self.embedding_model in n for n in model_names):
                    return True
                else:
                    logger.warning(
                        f"Embedding model '{self.embedding_model}' not found. "
                        f"Run: ollama pull {self.embedding_model}"
                    )
        except Exception as e:
            logger.warning(f"Failed to check embedding model: {e}")
        return False

    # ── Embeddings ────────────────────────────────────────────────────────────

    def _embed_one(self, text: str) -> List[float]:
        """Embed a single text — called from the thread pool."""
        if not self._embedding_available:
            return [0.0] * self._dimension

        try:
            r = self._session.post(
                f"{self.host}/api/embeddings",
                json={"model": self.embedding_model, "prompt": text[:2000]},
                timeout=_EMBED_TIMEOUT,
            )
            if r.status_code == 200:
                embedding = r.json().get("embedding", [0.0] * self._dimension)
                # Ensure correct dimension
                if len(embedding) != self._dimension:
                    logger.warning(f"Embedding dimension mismatch: expected {self._dimension}, got {len(embedding)}")
                    if len(embedding) > self._dimension:
                        embedding = embedding[:self._dimension]
                    else:
                        embedding = embedding + [0.0] * (self._dimension - len(embedding))
                return embedding
            elif r.status_code == 500:
                logger.warning(f"Ollama embedding HTTP 500 - model '{self.embedding_model}' may not exist")
                return [0.0] * self._dimension
            else:
                logger.error(f"Ollama embedding HTTP {r.status_code}")
        except requests.exceptions.Timeout:
            logger.error(f"Ollama embedding timeout for text length {len(text)}")
        except Exception as e:
            logger.error(f"Ollama embedding error: {e}")
        return [0.0] * self._dimension

    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Embed a batch of texts **concurrently** using a thread pool.
        Returns zero vectors if embedding fails (graceful degradation).
        """
        if not self.available or not self._embedding_available:
            logger.debug(f"Ollama embeddings unavailable, returning zero vectors for {len(texts)} texts")
            return np.zeros((len(texts), self._dimension))

        if not texts:
            return np.empty((0, self._dimension))

        workers = min(_EMBED_WORKERS, len(texts))
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(self._embed_one, texts))

        return np.array(results)

    def get_embedding(self, text: str) -> List[float]:
        """Embed a single text (convenience wrapper)."""
        if not self.available or not self._embedding_available:
            return [0.0] * self._dimension
        return self._embed_one(text)

    # ── Chat ──────────────────────────────────────────────────────────────────

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False,
    ) -> str:
        """
        Generate a chat completion.
        """
        if not self.available:
            raise RuntimeError("Ollama not available. Run 'ollama serve'")

        payload = {
            "model":    self.llm_model,
            "messages": messages,
            "stream":   stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": 2048,
            },
        }

        try:
            if stream:
                return self._chat_stream(payload)
            else:
                r = self._session.post(
                    f"{self.host}/api/chat",
                    json=payload,
                    timeout=_CHAT_TIMEOUT,
                )
                if r.status_code == 200:
                    content = r.json().get("message", {}).get("content", "").strip()
                    logger.info(f"[ollama] ✅ {self.llm_model} → {len(content)} chars")
                    return content
                logger.error(f"Ollama chat HTTP {r.status_code}: {r.text[:200]}")
                raise RuntimeError(f"Ollama returned {r.status_code}")

        except requests.exceptions.Timeout:
            logger.warning(f"[ollama] ⏰ {self.llm_model} timed out after {_CHAT_TIMEOUT}s")
            raise RuntimeError("Ollama chat timed out")
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Ollama — is 'ollama serve' running?")
            raise RuntimeError("Ollama connection failed")

    def _chat_stream(self, payload: dict) -> str:
        """Collect all streamed chunks and return the assembled string."""
        chunks: List[str] = []
        with self._session.post(
            f"{self.host}/api/chat",
            json=payload,
            stream=True,
            timeout=_CHAT_TIMEOUT,
        ) as r:
            r.raise_for_status()
            import json as _json
            for line in r.iter_lines():
                if not line:
                    continue
                try:
                    obj = _json.loads(line)
                    delta = obj.get("message", {}).get("content", "")
                    if delta:
                        chunks.append(delta)
                    if obj.get("done"):
                        break
                except Exception:
                    pass
        return "".join(chunks).strip()

    # ── Health ────────────────────────────────────────────────────────────────

    def health_check(self) -> Dict[str, Any]:
        if not self.available:
            return {"available": False, "error": "Ollama not running"}
        try:
            r = self._session.get(f"{self.host}/api/tags", timeout=_HEALTH_TIMEOUT)
            if r.status_code == 200:
                names = [m.get("name", "") for m in r.json().get("models", [])]
                return {
                    "available":             True,
                    "host":                  self.host,
                    "embedding_model_loaded": any(self.embedding_model in n for n in names),
                    "llm_model_loaded":       any(self.llm_model in n for n in names),
                    "available_models":       names[:10],
                }
        except Exception as e:
            return {"available": False, "error": str(e)}
        return {"available": False, "error": "Unknown"}


# ── Singleton ─────────────────────────────────────────────────────────────────

_ollama_service: Optional[OllamaService] = None


def get_ollama_service() -> OllamaService:
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = OllamaService()
    return _ollama_service