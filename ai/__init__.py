"""
ChemMind AI Subsystem Package
"""

from ai.config import settings, AISettings
from ai.generation.gateway import LLMGateway, gateway
from ai.ingestion import IngestionPipeline, PDFDocumentParser, BaseDocumentParser
from ai.chunking import LaTeXChemistryChunker, BaseChunker, extract_chemical_entities
from ai.vector_store import BaseVectorStore, QdrantVectorStore, MockVectorStore
from ai.embeddings import EmbeddingPipeline
from ai.retrieval import BaseRetriever, DenseRetriever
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
    VectorPoint,
    VectorSearchResult,
    RetrievalQuery,
    RetrievedChunk,
    RetrievalResponse,
)

__all__ = [
    "settings",
    "AISettings",
    "LLMGateway",
    "gateway",
    "IngestionPipeline",
    "PDFDocumentParser",
    "BaseDocumentParser",
    "LaTeXChemistryChunker",
    "BaseChunker",
    "extract_chemical_entities",
    "BaseVectorStore",
    "QdrantVectorStore",
    "MockVectorStore",
    "EmbeddingPipeline",
    "BaseRetriever",
    "DenseRetriever",
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
    "VectorPoint",
    "VectorSearchResult",
    "RetrievalQuery",
    "RetrievedChunk",
    "RetrievalResponse",
]
