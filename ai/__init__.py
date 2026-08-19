"""
ChemMind AI Subsystem Package
"""

from ai.config import settings, AISettings
from ai.generation.gateway import LLMGateway
from ai.ingestion import IngestionPipeline, PDFDocumentParser, BaseDocumentParser
from ai.chunking import LaTeXChemistryChunker, BaseChunker, extract_chemical_entities
from ai.schemas import (
    Role,
    ChatMessage,
    TokenUsage,
    LLMRequest,
    LLMResponse,
    StreamChunk,
    SourceLocation,
    Citation,
    DocumentMetadata,
    DocumentChunk,
    EmbeddingRequest,
    EmbeddingResponse,
    BlockType,
    ExtractedBlock,
    ParsedPage,
    IngestedDocument,
)

__all__ = [
    "settings",
    "AISettings",
    "LLMGateway",
    "IngestionPipeline",
    "PDFDocumentParser",
    "BaseDocumentParser",
    "LaTeXChemistryChunker",
    "BaseChunker",
    "extract_chemical_entities",
    "Role",
    "ChatMessage",
    "TokenUsage",
    "LLMRequest",
    "LLMResponse",
    "StreamChunk",
    "SourceLocation",
    "Citation",
    "DocumentMetadata",
    "DocumentChunk",
    "EmbeddingRequest",
    "EmbeddingResponse",
    "BlockType",
    "ExtractedBlock",
    "ParsedPage",
    "IngestedDocument",
]
