from unittest.mock import AsyncMock, patch
import httpx
import pytest
from ai.agentic.tools import WebSearchTool
from ai.providers.ollama_embedding import OllamaEmbeddingProvider
from ai.providers.ollama_llm import OllamaLLMProvider
from ai.schemas.embedding import EmbeddingRequest
from ai.schemas.llm import ChatMessage, LLMRequest, Role
from app.services.ai_gateway import AIGatewayService


@pytest.mark.asyncio
async def test_ollama_llm_provider_connection_error():
    # Point provider to dead port
    dead_provider = OllamaLLMProvider(base_url="http://127.0.0.1:59999", timeout=1.0)
    req = LLMRequest(
        messages=[ChatMessage(role=Role.USER, content="Test prompt")],
        model="llama3",
    )
    with pytest.raises(RuntimeError) as exc_info:
        await dead_provider.generate(req)
    assert "Ollama provider request error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ollama_llm_provider_http_500_error():
    provider = OllamaLLMProvider(base_url="http://localhost:11434")
    req = LLMRequest(
        messages=[ChatMessage(role=Role.USER, content="Trigger 500")],
        model="llama3",
    )

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error",
            request=httpx.Request("POST", "http://localhost:11434/api/chat"),
            response=httpx.Response(500),
        )
        mock_post.return_value = mock_response

        with pytest.raises(RuntimeError) as exc_info:
            await provider.generate(req)
        assert "Ollama provider request error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ollama_embedding_provider_connection_error():
    dead_emb_provider = OllamaEmbeddingProvider(base_url="http://127.0.0.1:59999", timeout=1.0)
    req = EmbeddingRequest(input_texts=["Test text for embedding"])
    with pytest.raises(RuntimeError) as exc_info:
        await dead_emb_provider.embed(req)
    assert "Ollama embedding request failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_web_search_tool_offline_fallback():
    web_tool = WebSearchTool(timeout=0.1)

    # Even if live web search fails or network is disconnected, fallback generator returns clean structured results
    with patch.object(web_tool, "_search_duckduckgo", return_value=[]), \
         patch.object(web_tool, "_search_pubchem", return_value=[]):
        results = await web_tool.search("enantioselective catalysis", max_results=3)

    assert len(results) == 3
    for r in results:
        assert r.source_type == "web"
        assert len(r.title) > 0
        assert r.url.startswith("https://")
        assert len(r.domain) > 0


@pytest.mark.asyncio
async def test_ai_gateway_resilient_fallback_on_engine_failure():
    gateway_service = AIGatewayService()
    # Force agentic_engine to raise an exception
    gateway_service.has_rag = True
    gateway_service.agentic_engine = AsyncMock()
    gateway_service.agentic_engine.execute.side_effect = RuntimeError("Simulated vector DB failure")

    # Gateway should fall back gracefully rather than crashing
    answer, citations = await gateway_service.generate_rag_response(
        prompt="Explain synthesis steps",
        workspace_id="ws_fail_001",
    )
    assert len(answer) > 0
    assert "ChemMind" in answer
    assert isinstance(citations, list)
    assert len(citations) >= 1
