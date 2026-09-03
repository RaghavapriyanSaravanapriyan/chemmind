import json
from typing import AsyncGenerator, Dict, Any, List
import httpx
from ai.config import settings
from ai.providers.base_llm import BaseLLMProvider
from ai.schemas.llm import LLMRequest, LLMResponse, StreamChunk, TokenUsage, ChatMessage
from ai.utils.logger import logger

class OllamaLLMProvider(BaseLLMProvider):
    """Concrete LLM Provider interfacing with local Ollama REST API."""

    def __init__(self, base_url: str = None, timeout: float = None):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.timeout = timeout or settings.httpx_timeout_seconds

    @property
    def provider_name(self) -> str:
        return "ollama"

    def _format_messages(self, messages: List[ChatMessage], system_prompt: str = None) -> List[Dict[str, str]]:
        formatted = []
        if system_prompt:
            formatted.append({"role": "system", "content": system_prompt})
        for msg in messages:
            formatted.append({"role": msg.role.value, "content": msg.content})
        return formatted

    async def generate(self, request: LLMRequest) -> LLMResponse:
        model = request.model or settings.default_llm_model
        payload = {
            "model": model,
            "messages": self._format_messages(request.messages, request.system_prompt),
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "top_p": request.top_p,
                **request.options
            }
        }

        url = f"{self.base_url}/api/chat"
        logger.debug(f"Ollama generate call to {url} with model {model}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPError as exc:
                logger.error(f"Ollama HTTP request failed: {exc}")
                raise RuntimeError(f"Ollama provider request error: {exc}") from exc

        content = data.get("message", {}).get("content", "")
        prompt_eval_count = data.get("prompt_eval_count", 0)
        eval_count = data.get("eval_count", 0)

        return LLMResponse(
            content=content,
            model=model,
            finish_reason=data.get("done_reason", "stop"),
            usage=TokenUsage(
                prompt_tokens=prompt_eval_count,
                completion_tokens=eval_count,
                total_tokens=prompt_eval_count + eval_count
            ),
            metadata={"raw": data}
        )

    async def stream(self, request: LLMRequest) -> AsyncGenerator[StreamChunk, None]:
        model = request.model or settings.default_llm_model
        payload = {
            "model": model,
            "messages": self._format_messages(request.messages, request.system_prompt),
            "stream": True,
            "options": {
                "temperature": request.temperature,
                "top_p": request.top_p,
                **request.options
            }
        }

        url = f"{self.base_url}/api/chat"
        logger.debug(f"Ollama stream call to {url} with model {model}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        
                        delta = data.get("message", {}).get("content", "")
                        is_done = data.get("done", False)

                        yield StreamChunk(
                            delta_content=delta,
                            finish_reason=data.get("done_reason") if is_done else None,
                            model=model,
                            is_final=is_done
                        )
            except httpx.HTTPError as exc:
                logger.error(f"Ollama streaming HTTP request failed: {exc}")
                raise RuntimeError(f"Ollama provider streaming error: {exc}") from exc

    async def list_models(self) -> List[Dict[str, Any]]:
        """Lists models installed in Ollama via GET /api/tags."""
        url = f"{self.base_url}/api/tags"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                models = data.get("models", [])
                # Normalise to [{name, size, details, capabilities}]
                out: List[Dict[str, Any]] = []
                for m in models:
                    out.append({
                        "name": m.get("name", ""),
                        "model": m.get("model", m.get("name", "")),
                        "size": m.get("size", 0),
                        "digest": m.get("digest", ""),
                        "details": m.get("details", {}),
                        "capabilities": m.get("capabilities", []),
                    })
                return out
            except httpx.HTTPError as exc:
                logger.error(f"Ollama list_models failed: {exc}")
                raise RuntimeError(f"Ollama list_models error: {exc}") from exc

    async def health_check(self) -> bool:
        try:
            models = await self.list_models()
            return True
        except Exception:
            return False
