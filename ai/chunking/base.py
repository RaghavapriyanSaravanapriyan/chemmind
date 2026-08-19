from abc import ABC, abstractmethod
from typing import List
from ai.schemas.document import DocumentChunk
from ai.schemas.ingestion import IngestedDocument

class BaseChunker(ABC):
    """Abstract interface for semantic chunking algorithms."""

    @abstractmethod
    def chunk_document(self, doc: IngestedDocument) -> List[DocumentChunk]:
        """Processes an IngestedDocument into a list of structure-aware DocumentChunks."""
        pass
