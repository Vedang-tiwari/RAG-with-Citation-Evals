import os
import numpy as np
from typing import List, Union
from backend.app.core.config import settings
from backend.app.core.logging import logger

class TextEmbedder:
    _instance = None
    _model = None
    _model_name = None

    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.DEFAULT_EMBEDDING_MODEL
        self.dimension = 384  # Standard dimension for all-MiniLM-L6-v2

    def _load_model(self):
        if TextEmbedder._model is None or TextEmbedder._model_name != self.model_name:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading embedding model: {self.model_name}")
                TextEmbedder._model = SentenceTransformer(self.model_name)
                TextEmbedder._model_name = self.model_name
                self.dimension = TextEmbedder._model.get_sentence_embedding_dimension()
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer ({e}). Falling back to deterministic dense vectorizer.")
                TextEmbedder._model = "fallback"
                TextEmbedder._model_name = "fallback"
                self.dimension = 384

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        self._load_model()

        if TextEmbedder._model != "fallback" and TextEmbedder._model is not None:
            try:
                embeddings = TextEmbedder._model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
                return embeddings.tolist()
            except Exception as e:
                logger.warning(f"Error encoding with SentenceTransformer: {e}. Falling back.")

        # Fallback deterministic dense vector generator for testing / offline environments
        return [self._fallback_embed(t) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        return self.embed_texts([query])[0]

    def _fallback_embed(self, text: str) -> List[float]:
        """
        Deterministic pseudo-embedding for testing when SentenceTransformer model isn't loaded.
        """
        vec = np.zeros(self.dimension, dtype=np.float32)
        words = text.lower().split()
        if not words:
            return vec.tolist()
        for idx, word in enumerate(words):
            h = hash(word) % self.dimension
            vec[h] += 1.0 / (idx + 1)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

embedder = TextEmbedder()

