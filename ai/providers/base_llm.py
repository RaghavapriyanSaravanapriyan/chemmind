from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Dict, Any
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

    async def list_models(self) -> List[Dict[str, Any]]:
        """Lists available models. Returns [{'name': str, ...}]. Defaults to empty."""
        return []

    async def health_check(self) -> bool:
        """Returns True if provider backend is reachable."""
        return True
