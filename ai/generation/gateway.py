from typing import AsyncGenerator, Dict, Optional
from ai.config import settings
from ai.providers.base_llm import BaseLLMProvider
from ai.providers.base_embedding import BaseEmbeddingProvider
from ai.providers.ollama_llm import OllamaLLMProvider
from ai.providers.mock_llm import MockLLMProvider
from ai.providers.ollama_embedding import OllamaEmbeddingProvider, MockEmbeddingProvider
from ai.schemas.llm import LLMRequest, LLMResponse, StreamChunk
from ai.schemas.embedding import EmbeddingRequest, EmbeddingResponse
from ai.utils.logger import logger

class LLMGateway:
    """
    Provider-independent LLM Gateway.
    Application logic interacts solely with LLMGateway, remaining completely
    decoupled from specific LLM backend implementations.
    """

    def __init__(
        self,
        llm_provider: Optional[BaseLLMProvider] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None
    ):
        self._llm_providers: Dict[str, BaseLLMProvider] = {}
        self._embedding_providers: Dict[str, BaseEmbeddingProvider] = {}

        # Register default providers
        self.register_llm_provider(OllamaLLMProvider())
        self.register_llm_provider(MockLLMProvider())

        self.register_embedding_provider(OllamaEmbeddingProvider())
        self.register_embedding_provider(MockEmbeddingProvider())

        # Set active providers
        self._active_llm_provider_name = settings.ai_provider
        self._active_embedding_provider_name = settings.embedding_provider

        if llm_provider:
            self.register_llm_provider(llm_provider)
            self._active_llm_provider_name = llm_provider.provider_name

        if embedding_provider:
            self.register_embedding_provider(embedding_provider)
            self._active_embedding_provider_name = embedding_provider.provider_name

    def register_llm_provider(self, provider: BaseLLMProvider) -> None:
        """Registers a new LLM provider instance."""
        self._llm_providers[provider.provider_name.lower()] = provider
        logger.info(f"Registered LLM Provider: {provider.provider_name}")

    def register_embedding_provider(self, provider: BaseEmbeddingProvider) -> None:
        """Registers a new Embedding provider instance."""
        self._embedding_providers[provider.provider_name.lower()] = provider
        logger.info(f"Registered Embedding Provider: {provider.provider_name}")

    def set_active_llm_provider(self, name: str) -> None:
        """Sets the active LLM provider by name."""
        name_lower = name.lower()
        if name_lower not in self._llm_providers:
            raise ValueError(f"LLM Provider '{name}' is not registered. Available: {list(self._llm_providers.keys())}")
        self._active_llm_provider_name = name_lower
        logger.info(f"Active LLM Provider switched to: {name_lower}")

    def set_active_embedding_provider(self, name: str) -> None:
        """Sets the active Embedding provider by name."""
        name_lower = name.lower()
        if name_lower not in self._embedding_providers:
            raise ValueError(f"Embedding Provider '{name}' is not registered. Available: {list(self._embedding_providers.keys())}")
        self._active_embedding_provider_name = name_lower
        logger.info(f"Active Embedding Provider switched to: {name_lower}")

    def get_llm_provider(self, name: Optional[str] = None) -> BaseLLMProvider:
        """Returns requested or active LLM provider."""
        provider_name = (name or self._active_llm_provider_name).lower()
        provider = self._llm_providers.get(provider_name)
        if not provider:
            raise RuntimeError(f"LLM Provider '{provider_name}' not found.")
        return provider

    def get_embedding_provider(self, name: Optional[str] = None) -> BaseEmbeddingProvider:
        """Returns requested or active Embedding provider."""
        provider_name = (name or self._active_embedding_provider_name).lower()
        provider = self._embedding_providers.get(provider_name)
        if not provider:
            raise RuntimeError(f"Embedding Provider '{provider_name}' not found.")
        return provider

    async def generate(self, request: LLMRequest, provider_name: Optional[str] = None) -> LLMResponse:
        """Executes LLM completion using the configured provider."""
        provider = self.get_llm_provider(provider_name)
        return await provider.generate(request)

    async def stream(self, request: LLMRequest, provider_name: Optional[str] = None) -> AsyncGenerator[StreamChunk, None]:
        """Executes streaming LLM completion using the configured provider."""
        provider = self.get_llm_provider(provider_name)
        async for chunk in provider.stream(request):
            yield chunk

    async def embed(self, request: EmbeddingRequest, provider_name: Optional[str] = None) -> EmbeddingResponse:
        """Generates embeddings using the configured embedding provider."""
        provider = self.get_embedding_provider(provider_name)
        return await provider.embed(request)
