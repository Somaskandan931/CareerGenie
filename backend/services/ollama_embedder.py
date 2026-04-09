"""
Ollama Embedder - drop-in replacement for SentenceTransformer
Optimized:
  - Reuses a shared OllamaService (connection pool / keep-alive)
  - Encodes batches concurrently instead of serially
"""
import logging
import numpy as np
from typing import List, Union

logger = logging.getLogger(__name__)


class OllamaEmbedder:
    def __init__(
        self,
        model_name: str = "all-minilm",
        host: str = "http://localhost:11434",
    ):
        self.model_name  = model_name
        self.host        = host
        self._dimension  = 384  # all-minilm → 384-dim vectors

        # Reuse the shared OllamaService so we share its connection pool
        from backend.services.ollama_service import get_ollama_service
        self._svc = get_ollama_service()

        logger.info(f"OllamaEmbedder initialised — model={model_name}")

    # ── Public API (matches SentenceTransformer.encode signature) ─────────────

    def encode(
        self,
        texts: Union[str, List[str]],
        convert_to_numpy: bool = True,
        batch_size: int = 32,       # kept for API compat; we use thread pool internally
        show_progress_bar: bool = False,
    ) -> np.ndarray:
        """
        Encode one or more texts.
        Batches are processed concurrently via OllamaService.get_embeddings().
        """
        if isinstance(texts, str):
            texts = [texts]

        embeddings = self._svc.get_embeddings(texts)

        if convert_to_numpy:
            return embeddings
        return embeddings.tolist()

    def encode_single(self, text: str) -> List[float]:
        """Encode a single text string (convenience)."""
        return self._svc.get_embedding(text)