import asyncio
from typing import AsyncGenerator, List, Dict, Any
from ai.providers.base_llm import BaseLLMProvider
from ai.schemas.llm import LLMRequest, LLMResponse, StreamChunk, TokenUsage

class MockLLMProvider(BaseLLMProvider):
    """Mock LLM Provider for unit testing and offline development."""

    def __init__(self, mock_response: str = "This is a mock response from ChemMind LLM Gateway."):
        self._mock_response = mock_response

    @property
    def provider_name(self) -> str:
        return "mock"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        model = request.model or "mock-model"
        prompt_len = sum(len(m.content) for m in request.messages)
        return LLMResponse(
            content=self._mock_response,
            model=model,
            finish_reason="stop",
            usage=TokenUsage(
                prompt_tokens=prompt_len // 4,
                completion_tokens=len(self._mock_response) // 4,
                total_tokens=(prompt_len + len(self._mock_response)) // 4
            )
        )

    async def stream(self, request: LLMRequest) -> AsyncGenerator[StreamChunk, None]:
        model = request.model or "mock-model"
        words = self._mock_response.split(" ")
        for i, word in enumerate(words):
            chunk_text = word + (" " if i < len(words) - 1 else "")
            is_last = (i == len(words) - 1)
            yield StreamChunk(
                delta_content=chunk_text,
                finish_reason="stop" if is_last else None,
                model=model,
                is_final=is_last
            )
            await asyncio.sleep(0.01)

    async def list_models(self) -> List[Dict[str, Any]]:
        return [{"name": "mock-model", "model": "mock-model", "capabilities": ["completion"]}]

    async def health_check(self) -> bool:
        return True
