"""
Ollama Embedder - Replacement for SentenceTransformer
"""
import logging
import ollama
import numpy as np
from typing import List

logger = logging.getLogger( __name__ )


class OllamaEmbedder :
    def __init__ ( self, model_name: str = "all-minilm", host: str = "http://localhost:11434" ) :
        self.model_name = model_name
        self.host = host
        self._dimension = 384  # all-minilm produces 384-dim vectors
        logger.info( f"OllamaEmbedder initialized with model: {model_name}" )

    def encode ( self, texts: List[str], convert_to_numpy: bool = True ) -> np.ndarray :
        """Generate embeddings for a list of texts using Ollama"""
        embeddings = []

        for text in texts :
            try :
                response = ollama.embeddings(
                    model=self.model_name,
                    prompt=text
                )
                embedding = response['embedding']
                embeddings.append( embedding )
            except Exception as e :
                logger.error( f"Ollama embedding failed: {e}" )
                # Fallback to zero vector
                embeddings.append( [0.0] * self._dimension )

        if convert_to_numpy :
            return np.array( embeddings )
        return embeddings

    def encode_single ( self, text: str ) -> List[float] :
        """Encode a single text string"""
        response = ollama.embeddings( model=self.model_name, prompt=text )
        return response['embedding']