"""
ChemMind AI Subsystem Package
"""

from ai.config import settings, AISettings
from ai.generation.gateway import LLMGateway, gateway
from ai.generation.rag_service import RAGGenerationService
from ai.ingestion import IngestionPipeline, PDFDocumentParser, BaseDocumentParser
from ai.chunking import LaTeXChemistryChunker, BaseChunker, extract_chemical_entities
from ai.vector_store import BaseVectorStore, QdrantVectorStore, MockVectorStore
from ai.embeddings import EmbeddingPipeline
from ai.retrieval import BaseRetriever, DenseRetriever, BM25KeywordRetriever, HybridRetriever, reciprocal_rank_fusion
from ai.prompts import CHEMISTRY_RAG_SYSTEM_PROMPT, build_rag_prompt
from ai.citations import CitationResolver
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
    RAGRequest,
    RAGResponse,
    CitationMap,
    CitedRAGResponse,
)

__all__ = [
    "settings",
    "AISettings",
    "LLMGateway",
    "gateway",
    "RAGGenerationService",
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
    "BM25KeywordRetriever",
    "HybridRetriever",
    "reciprocal_rank_fusion",
    "CHEMISTRY_RAG_SYSTEM_PROMPT",
    "build_rag_prompt",
    "CitationResolver",
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
    "RAGRequest",
    "RAGResponse",
    "CitationMap",
    "CitedRAGResponse",
]
