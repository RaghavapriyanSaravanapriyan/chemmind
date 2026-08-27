from abc import ABC, abstractmethod
from ai.schemas.retrieval import RetrievalQuery, RetrievalResponse

class BaseRetriever(ABC):
    """Abstract interface for RAG document retrieval engines."""

    @abstractmethod
    async def retrieve(self, query: RetrievalQuery) -> RetrievalResponse:
        """Retrieves candidate document chunks matching the retrieval query."""
        pass
