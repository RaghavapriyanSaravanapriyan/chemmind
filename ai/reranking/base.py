from abc import ABC, abstractmethod
from ai.schemas.rerank import RerankRequest, RerankResponse

class BaseReranker(ABC):
    """Abstract interface for Reranking engines."""

    @abstractmethod
    async def rerank(self, request: RerankRequest) -> RerankResponse:
        """Re-scores and re-ranks a list of candidate chunks."""
        pass
