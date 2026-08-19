"""
ChemMind AI Package Foundation
"""

from ai.config import settings, AISettings
from ai.generation.gateway import LLMGateway
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
)

__all__ = [
    "settings",
    "AISettings",
    "LLMGateway",
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
]
