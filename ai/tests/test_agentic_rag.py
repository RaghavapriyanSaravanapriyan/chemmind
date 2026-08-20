import pytest
from ai.agentic import (
    AgenticRAGEngine,
    AgenticRouter,
    ChemistryPropertyTool,
    RoutingDecision,
    RoutingMode,
    WebSearchResult,
    WebSearchTool,
)
from ai.citations.resolver import CitationResolver
from ai.retrieval.dense import DenseRetriever
from ai.schemas.rag import RAGRequest
from ai.schemas.retrieval import RetrievedChunk
from ai.vector_store import MockVectorStore


@pytest.mark.asyncio
async def test_web_search_tool_fallback_and_structure():
    tool = WebSearchTool()
    results = await tool.search("catalytic hydrogenation of alkenes", max_results=3)

    assert len(results) > 0
    first = results[0]
    assert isinstance(first, WebSearchResult)
    assert first.url.startswith("http")
    assert len(first.title) > 0
    assert first.domain != ""
    assert first.source_type == "web"


@pytest.mark.asyncio
async def test_chemistry_property_tool():
    tool = ChemistryPropertyTool()
    res = await tool.lookup("benzene")
    assert res["compound"] == "benzene"
    assert "found" in res


def test_agentic_router_internal_docs_sufficient():
    router = AgenticRouter(sufficiency_threshold=0.30)
    chunk = RetrievedChunk(
        chunk_id="c1",
        score=0.85,
        text="Aspirin (acetylsalicylic acid) is synthesized via acetylation of salicylic acid.",
        document_id="doc1",
        workspace_id="ws1",
        page_number=1,
    )
    decision = router.evaluate("How is aspirin synthesized?", [chunk])

    assert decision.mode == RoutingMode.INTERNAL_ONLY
    assert decision.should_use_web is False


def test_agentic_router_triggers_web_when_no_docs():
    router = AgenticRouter(sufficiency_threshold=0.30)
    decision = router.evaluate("What is the latest 2026 update on quantum dot catalysts?", [])

    assert decision.should_use_web is True
    assert decision.mode in [RoutingMode.WEB_FALLBACK, RoutingMode.HYBRID_AUGMENTED]


def test_agentic_router_triggers_web_when_low_score():
    router = AgenticRouter(sufficiency_threshold=0.50)
    chunk = RetrievedChunk(
        chunk_id="c1",
        score=0.15,
        text="Irrelevant paper fragment.",
        document_id="doc1",
        workspace_id="ws1",
        page_number=1,
    )
    decision = router.evaluate("Explain Suzuki-Miyaura coupling mechanism", [chunk])

    assert decision.should_use_web is True
    assert decision.mode == RoutingMode.WEB_FALLBACK


def test_citation_resolver_parses_web_clickable_links():
    resolver = CitationResolver()
    answer_text = (
        "Suzuki coupling uses palladium catalysts [1]. "
        "Further details are available at [PubChem Compound](https://pubchem.ncbi.nlm.nih.gov/#query=benzene) "
        "and [Nature Chemistry](https://www.nature.com/articles/s41557-023-00000)."
    )

    doc_chunk = RetrievedChunk(
        chunk_id="c1",
        score=0.9,
        text="Suzuki coupling reaction mechanism overview.",
        document_id="doc_suzuki.pdf",
        workspace_id="ws1",
        page_number=3,
    )

    web_results = [
        WebSearchResult(
            title="PubChem Compound",
            url="https://pubchem.ncbi.nlm.nih.gov/#query=benzene",
            domain="pubchem.ncbi.nlm.nih.gov",
            snippet="Benzene compound record.",
            source_type="web"
        )
    ]

    cit_map = resolver.resolve_citations(answer_text, [doc_chunk], web_results=web_results, workspace_id="ws1")

    assert len(cit_map.citations) >= 2
    web_cits = [c for c in cit_map.citations if c.source_type == "web"]
    assert len(web_cits) >= 1
    assert web_cits[0].url.startswith("https://")
    assert web_cits[0].domain != ""


@pytest.mark.asyncio
async def test_agentic_rag_engine_end_to_end():
    from ai.generation.gateway import LLMGateway
    from ai.providers.mock_llm import MockLLMProvider
    from ai.providers.ollama_embedding import MockEmbeddingProvider

    gateway = LLMGateway()
    gateway.register_llm_provider(MockLLMProvider())
    gateway.register_embedding_provider(MockEmbeddingProvider())
    gateway.set_active_llm_provider("mock")
    gateway.set_active_embedding_provider("mock")

    vstore = MockVectorStore()
    retriever = DenseRetriever(vector_store=vstore, llm_gateway=gateway)
    engine = AgenticRAGEngine(retriever=retriever, llm_gateway=gateway)

    req = RAGRequest(
        query_text="What are the recent web publications on graphene synthesis?",
        workspace_id="ws_agentic_test",
        enable_web_search=True,
    )

    response = await engine.execute(req)

    assert response.workspace_id == "ws_agentic_test"
    assert len(response.answer) > 0
    assert response.routing_mode is not None
    assert len(response.web_results) > 0
    assert len(response.citations) > 0
