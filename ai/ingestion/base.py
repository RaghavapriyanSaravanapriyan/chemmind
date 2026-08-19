from abc import ABC, abstractmethod
from typing import Union, BinaryIO
from ai.schemas.ingestion import IngestedDocument

class BaseDocumentParser(ABC):
    """Abstract interface for document parsers (PDF, LaTeX, Markdown, HTML, etc.)."""

    @property
    @abstractmethod
    def supported_mime_types(self) -> list[str]:
        """List of supported MIME types (e.g. ['application/pdf'])."""
        pass

    @abstractmethod
    async def parse_file(
        self,
        file_path: str,
        workspace_id: str,
        document_id: str
    ) -> IngestedDocument:
        """Parses a document file on disk and returns structured IngestedDocument."""
        pass

    @abstractmethod
    async def parse_bytes(
        self,
        file_bytes: bytes,
        filename: str,
        workspace_id: str,
        document_id: str
    ) -> IngestedDocument:
        """Parses in-memory document bytes and returns structured IngestedDocument."""
        pass
