import os
from typing import Dict, Optional, Union
from ai.ingestion.base import BaseDocumentParser
from ai.ingestion.pdf_parser import PDFDocumentParser
from ai.schemas.ingestion import IngestedDocument
from ai.utils.logger import logger

class IngestionPipeline:
    """
    Ingestion Pipeline orchestrator.
    Routes document parsing based on MIME type or file extension to the registered BaseDocumentParser.
    """

    def __init__(self):
        self._parsers: Dict[str, BaseDocumentParser] = {}
        # Register default PDF parser
        self.register_parser(PDFDocumentParser())

    def register_parser(self, parser: BaseDocumentParser) -> None:
        """Registers a parser for its supported MIME types."""
        for mime in parser.supported_mime_types:
            self._parsers[mime.lower()] = parser
            logger.info(f"Registered document parser '{parser.__class__.__name__}' for MIME type '{mime}'")

    def _detect_mime_type(self, filename: str, mime_type: Optional[str] = None) -> str:
        if mime_type:
            return mime_type.lower()
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".pdf":
            return "application/pdf"
        elif ext in [".txt", ".md", ".markdown"]:
            return "text/plain"
        return "application/octet-stream"

    def get_parser(self, mime_type: str) -> BaseDocumentParser:
        mime = mime_type.lower()
        parser = self._parsers.get(mime)
        if not parser:
            raise ValueError(
                f"Unsupported document format '{mime}'. Available parsers: {list(self._parsers.keys())}"
            )
        return parser

    async def ingest_file(
        self,
        file_path: str,
        workspace_id: str,
        document_id: str,
        mime_type: Optional[str] = None
    ) -> IngestedDocument:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        filename = os.path.basename(file_path)
        detected_mime = self._detect_mime_type(filename, mime_type)
        parser = self.get_parser(detected_mime)
        
        logger.info(f"Starting ingestion for file '{file_path}' (MIME: {detected_mime})")
        return await parser.parse_file(file_path, workspace_id, document_id)

    async def ingest_bytes(
        self,
        file_bytes: bytes,
        filename: str,
        workspace_id: str,
        document_id: str,
        mime_type: Optional[str] = None
    ) -> IngestedDocument:
        if not file_bytes:
            raise ValueError("Empty file bytes provided for ingestion.")
        
        detected_mime = self._detect_mime_type(filename, mime_type)
        parser = self.get_parser(detected_mime)
        
        logger.info(f"Starting ingestion for bytes (filename: '{filename}', MIME: {detected_mime})")
        return await parser.parse_bytes(file_bytes, filename, workspace_id, document_id)
