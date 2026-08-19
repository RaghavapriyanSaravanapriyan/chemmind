from abc import ABC, abstractmethod
from typing import AsyncGenerator
from ai.schemas.llm import LLMRequest, LLMResponse, StreamChunk

class BaseLLMProvider(ABC):
    """Abstract interface for LLM providers (Ollama, OpenAI, Anthropic, Mock, etc.)"""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns provider identifier name."""
        pass

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Executes a synchronous completion request."""
        pass

    @abstractmethod
    async def stream(self, request: LLMRequest) -> AsyncGenerator[StreamChunk, None]:
        """Executes a streaming completion request returning chunks as they arrive."""
        pass
