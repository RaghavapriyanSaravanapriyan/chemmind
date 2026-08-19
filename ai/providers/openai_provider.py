import json
from typing import AsyncGenerator, List, Optional
import httpx
from ai.config import settings
from ai.providers.base_embedding import BaseEmbeddingProvider
from ai.providers.base_llm import BaseLLMProvider
from ai.schemas.embedding import EmbeddingRequest, EmbeddingResponse
from ai.schemas.llm import LLMRequest, LLMResponse, StreamChunk, TokenUsage
from ai.utils.logger import logger

class OpenAILLMProvider(BaseLLMProvider):
    """
    OpenAI-Compatible Cloud LLM Provider.
    Supports OpenAI, OpenRouter, Groq, Gemini OpenAI endpoint, vLLM, and Anyscale.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.openai_api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = (base_url or settings.openai_base_url).rstrip("/")
        self.client = httpx.AsyncClient(timeout=settings.httpx_timeout_seconds)

    @property
    def provider_name(self) -> str:
        return "openai"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        url = f"{self.base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        messages_payload = [{"role": msg.role.value, "content": msg.content} for msg in request.messages]
        payload = {
            "model": request.model or "gpt-4o-mini",
            "messages": messages_payload,
            "temperature": request.temperature,
            "stream": False,
        }
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens

        logger.info(f"Sending OpenAI API completion request to '{url}' with model '{payload['model']}'")

        try:
            resp = await self.client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            choice = data["choices"][0]
            content = choice["message"]["content"]
            finish_reason = choice.get("finish_reason", "stop")

            usage_data = data.get("usage", {})
            usage = TokenUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            )

            return LLMResponse(
                content=content,
                model=data.get("model", payload["model"]),
                finish_reason=finish_reason,
                usage=usage,
            )
        except Exception as e:
            logger.error(f"OpenAI LLM provider error: {str(e)}")
            raise

    async def stream(self, request: LLMRequest) -> AsyncGenerator[StreamChunk, None]:
        url = f"{self.base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        messages_payload = [{"role": msg.role.value, "content": msg.content} for msg in request.messages]
        payload = {
            "model": request.model or "gpt-4o-mini",
            "messages": messages_payload,
            "temperature": request.temperature,
            "stream": True,
        }

        try:
            async with self.client.stream("POST", url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    line = line.strip()
                    if not line or line.startswith(":"):
                        continue
                    if line.startswith("data: "):
                        line_data = line[6:].strip()
                        if line_data == "[DONE]":
                            yield StreamChunk(delta_content="", is_final=True, finish_reason="stop")
                            break
                        try:
                            chunk_obj = json.loads(line_data)
                            delta = chunk_obj["choices"][0]["delta"].get("content", "")
                            finish_reason = chunk_obj["choices"][0].get("finish_reason")
                            yield StreamChunk(
                                delta_content=delta,
                                model=chunk_obj.get("model"),
                                finish_reason=finish_reason,
                                is_final=finish_reason is not None
                            )
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"OpenAI LLM streaming error: {str(e)}")
            raise

import os

class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    OpenAI-Compatible Dense Vector Embedding Provider.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.openai_api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = (base_url or settings.openai_base_url).rstrip("/")
        self.client = httpx.AsyncClient(timeout=settings.httpx_timeout_seconds)

    @property
    def provider_name(self) -> str:
        return "openai"

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        url = f"{self.base_url}/embeddings"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        model_name = request.model or "text-embedding-3-small"
        payload = {
            "model": model_name,
            "input": request.input_texts,
        }

        logger.info(f"Sending OpenAI embedding request for {len(request.input_texts)} texts")

        try:
            resp = await self.client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            embeddings_list = [item["embedding"] for item in data["data"]]
            dimension = len(embeddings_list[0]) if embeddings_list else 1536

            return EmbeddingResponse(
                embeddings=embeddings_list,
                model=data.get("model", model_name),
                dimension=dimension
            )
        except Exception as e:
            logger.error(f"OpenAI Embedding provider error: {str(e)}")
            raise
