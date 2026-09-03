from typing import List, Dict, Any
import httpx
from ai.config import settings
from ai.providers.base_embedding import BaseEmbeddingProvider
from ai.schemas.embedding import EmbeddingRequest, EmbeddingResponse
from ai.utils.logger import logger

class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    """Concrete Embedding Provider interfacing with local Ollama REST API."""

    def __init__(self, base_url: str = None, timeout: float = None):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.timeout = timeout or settings.httpx_timeout_seconds

    @property
    def provider_name(self) -> str:
        return "ollama"

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        model = request.model or settings.default_embedding_model
        url = f"{self.base_url}/api/embed"
        
        payload = {
            "model": model,
            "input": request.input_texts
        }
        
        logger.debug(f"Ollama embed call to {url} for {len(request.input_texts)} texts")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                embeddings = data.get("embeddings", [])
            except httpx.HTTPError as exc:
                logger.error(f"Ollama embedding HTTP request failed: {exc}")
                raise RuntimeError(f"Ollama embedding provider error: {exc}") from exc

        return EmbeddingResponse(
            embeddings=embeddings,
            model=model,
            total_tokens=data.get("prompt_eval_count")
        )

    async def list_models(self) -> List[Dict[str, Any]]:
        """Lists embedding-capable models via Ollama /api/tags (filters capability 'embedding')."""
        url = f"{self.base_url}/api/tags"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                out: List[Dict[str, Any]] = []
                for m in data.get("models", []):
                    caps = m.get("capabilities", [])
                    # Include all models; caller can filter. Mark embedding-capable.
                    out.append({
                        "name": m.get("name", ""),
                        "model": m.get("model", m.get("name", "")),
                        "size": m.get("size", 0),
                        "capabilities": caps,
                        "embedding_capable": "embedding" in caps,
                        "details": m.get("details", {}),
                    })
                return out
            except httpx.HTTPError as exc:
                logger.error(f"Ollama embedding list_models failed: {exc}")
                raise RuntimeError(f"Ollama embedding list_models error: {exc}") from exc

    async def health_check(self) -> bool:
        try:
            await self.list_models()
            return True
        except Exception:
            return False

class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Mock Embedding Provider for unit testing."""

    def __init__(self, vector_dim: int = 384):
        self.vector_dim = vector_dim

    @property
    def provider_name(self) -> str:
        return "mock"

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        model = request.model or "mock-embedding-model"
        # Generate dummy deterministic floats derived from string length
        embeddings: List[List[float]] = []
        for text in request.input_texts:
            val = float(len(text) % 100) / 100.0
            vec = [val] * self.vector_dim
            embeddings.append(vec)

        return EmbeddingResponse(
            embeddings=embeddings,
            model=model,
            total_tokens=len(request.input_texts) * 5
        )

    async def list_models(self) -> List[Dict[str, Any]]:
        return [{"name": "mock-embedding-model", "model": "mock-embedding-model", "capabilities": ["embedding"]}]

    async def health_check(self) -> bool:
        return True
