from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ai.schemas.embedding import EmbeddingRequest, EmbeddingResponse

class BaseEmbeddingProvider(ABC):
    """Abstract interface for text embedding providers (Ollama, SentenceTransformers, OpenAI, etc.)"""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns provider identifier name."""
        pass

    @abstractmethod
    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generates vector embeddings for a list of input texts."""
        pass

    async def list_models(self) -> List[Dict[str, Any]]:
        """Lists available embedding models. Returns [{'name': str, ...}]."""
        return []

    async def health_check(self) -> bool:
        """Returns True if provider backend is reachable."""
        return True
