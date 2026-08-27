from abc import ABC, abstractmethod
from typing import List, Optional
from ai.schemas.vector import VectorPoint, VectorSearchResult

class BaseVectorStore(ABC):
    """Abstract interface for Vector Database providers (Qdrant, Mock, Chroma, etc.)."""

    @property
    @abstractmethod
    def store_name(self) -> str:
        """Returns vector store provider identifier name."""
        pass

    @abstractmethod
    async def create_collection(self, collection_name: str, vector_size: int) -> bool:
        """Creates a collection if it does not already exist."""
        pass

    @abstractmethod
    async def upsert_points(self, collection_name: str, points: List[VectorPoint]) -> bool:
        """Upserts a list of vector points with payloads into the collection."""
        pass

    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        workspace_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None
    ) -> List[VectorSearchResult]:
        """Performs vector similarity search with workspace and document filtering."""
        pass

    @abstractmethod
    async def delete_collection(self, collection_name: str) -> bool:
        """Deletes an entire collection."""
        pass
