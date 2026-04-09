"""
Ollama Service - Local LLM and Embeddings Provider
"""
import logging
import numpy as np
import requests
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class OllamaService:
    """Centralized service for Ollama operations using HTTP API directly"""

    def __init__(self, host: str = "http://localhost:11434",
                 embedding_model: str = "all-minilm",
                 llm_model: str = "llama3.2:3b"):
        self.host = host
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self._dimension = 384
        self.available = self._check_availability()

        if self.available:
            logger.info(f"OllamaService initialized: embedding={embedding_model}, llm={llm_model}, host={host}")
        else:
            logger.warning(f"Ollama not available at {host}. Run 'ollama serve' first.")

    def _check_availability(self) -> bool:
        """Check if Ollama is running and models are available"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m.get('name', '') for m in models]
                logger.info(f"Ollama available. Models: {model_names}")
                return True
        except Exception as e:
            logger.debug(f"Ollama check failed: {e}")
        return False

    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts using Ollama API"""
        if not self.available:
            raise RuntimeError("Ollama not available. Run 'ollama serve'")

        embeddings = []
        for text in texts:
            try:
                response = requests.post(
                    f"{self.host}/api/embeddings",
                    json={
                        "model": self.embedding_model,
                        "prompt": text[:2000]  # Limit text length
                    },
                    timeout=30
                )
                if response.status_code == 200:
                    embedding = response.json().get('embedding', [0.0] * self._dimension)
                    embeddings.append(embedding)
                else:
                    logger.error(f"Ollama embedding failed: {response.status_code}")
                    embeddings.append([0.0] * self._dimension)
            except Exception as e:
                logger.error(f"Ollama embedding error: {e}")
                embeddings.append([0.0] * self._dimension)

        return np.array(embeddings)

    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        if not self.available:
            raise RuntimeError("Ollama not available")

        try:
            response = requests.post(
                f"{self.host}/api/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": text[:2000]
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get('embedding', [0.0] * self._dimension)
        except Exception as e:
            logger.error(f"Ollama embedding error: {e}")

        return [0.0] * self._dimension

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7,
             max_tokens: int = 1024) -> str:
        """Generate chat completion using Ollama API"""
        if not self.available:
            raise RuntimeError("Ollama not available. Run 'ollama serve'")

        try:
            response = requests.post(
                f"{self.host}/api/chat",
                json={
                    "model": self.llm_model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    }
                },
                timeout=60
            )

            if response.status_code == 200:
                return response.json().get('message', {}).get('content', '').strip()
            else:
                logger.error(f"Ollama chat failed: {response.status_code} - {response.text}")
                raise RuntimeError(f"Ollama returned {response.status_code}")
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Ollama. Make sure it's running: 'ollama serve'")
            raise RuntimeError("Ollama connection failed")
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            raise

    def health_check(self) -> Dict[str, Any]:
        """Check if Ollama is running and models are available"""
        if not self.available:
            return {"available": False, "error": "Ollama not running"}

        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m.get('name', '') for m in models]

                return {
                    "available": True,
                    "host": self.host,
                    "embedding_model_loaded": any(self.embedding_model in m for m in model_names),
                    "llm_model_loaded": any(self.llm_model in m for m in model_names),
                    "available_models": model_names[:10]
                }
        except Exception as e:
            return {"available": False, "error": str(e)}

        return {"available": False, "error": "Unknown"}


# Singleton instance
_ollama_service = None

def get_ollama_service() -> OllamaService:
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = OllamaService()
    return _ollama_service