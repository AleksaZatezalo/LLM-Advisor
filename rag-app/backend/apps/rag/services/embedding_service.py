"""
Embedding Service.

Generates embeddings using sentence-transformers for offline operation.
"""
from functools import lru_cache
from sentence_transformers import SentenceTransformer
from django.conf import settings


class EmbeddingService:
    """
    Generates text embeddings using sentence-transformers.
    
    Uses a singleton pattern to avoid reloading the model on each request.
    The model runs entirely offline after initial download.
    """
    
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._model is None:
            self._load_model()
    
    def _load_model(self):
        """Load the embedding model. Called once on first use."""
        model_name = settings.EMBEDDING_MODEL
        self._model = SentenceTransformer(model_name)
    
    @property
    def dimension(self) -> int:
        """Return the embedding dimension size."""
        return self._model.get_sentence_embedding_dimension()
    
    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in batch."""
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    """Factory function to get the singleton embedding service."""
    return EmbeddingService()
