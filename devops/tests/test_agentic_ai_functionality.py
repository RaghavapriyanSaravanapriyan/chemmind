import pytest
from ai.agentic.agent import AgenticRAGEngine
from ai.agentic.router import AgenticRouter, RoutingMode
from ai.generation.gateway import LLMGateway
from ai.providers.mock_llm import MockLLMProvider
from ai.providers.ollama_embedding import MockEmbeddingProvider
from ai.retrieval.dense import DenseRetriever
from ai.schemas.rag import RAGRequest
from ai.schemas.retrieval import RetrievedChunk
from ai.vector_store.mock_store import MockVectorStore
from ai.vector_store.base import VectorItem


@pytest.fixture
def agentic_router():
    return AgenticRouter(sufficiency_threshold=0.30)


@pytest.fixture
def mock_agentic_engine():
    gateway = LLMGateway(
        llm_provider=MockLLMProvider(),
        embedding_provider=MockEmbeddingProvider(dimension=128),
    )
    vstore = MockVectorStore()
    vstore.upsert(
        "chemmind_chunks",
        [
            VectorItem(
                chunk_id="c1",
                document_id="doc1",
                workspace_id="ws1",
                vector=[0.1] * 128,
                text="The experimental NMR data for compound 4a shows a singlet at 3.8 ppm [1].",
                page_number=2,
                section_title="NMR Results",
            )
        ],
    )
    retriever = DenseRetriever(vector_store=vstore, llm_gateway=gateway)
    return AgenticRAGEngine(retriever=retriever, llm_gateway=gateway)


def test_agentic_router_explicit_web_keywords(agentic_router: AgenticRouter):
    decision = agentic_router.evaluate(
        query="Check PubMed for the latest 2026 clinical trials on this kinase inhibitor",
        retrieved_chunks=[],
    )
    assert decision.should_use_web is True
    assert decision.mode in [RoutingMode.WEB_FALLBACK, RoutingMode.HYBRID_AUGMENTED]
    assert "explicit" in decision.reason.lower()


def test_agentic_router_force_web_flag(agentic_router: AgenticRouter):
    decision = agentic_router.evaluate(
        query="What is the reaction yield?",
        retrieved_chunks=[],
        force_web=True,
    )
    assert decision.should_use_web is True
    assert decision.confidence == 1.0


def test_agentic_router_low_sufficiency_triggers_web(agentic_router: AgenticRouter):
    low_score_chunks = [
        RetrievedChunk(
            chunk_id="c_low",
            document_id="d1",
            workspace_id="w1",
            score=0.15,  # below 0.30 threshold
            text="General remarks on laboratory glassware cleaning.",
            page_number=1,
        )
    ]
    decision = agentic_router.evaluate(
        query="What is the activation barrier Delta G double dagger?",
        retrieved_chunks=low_score_chunks,
    )
    assert decision.should_use_web is True
    assert decision.mode == RoutingMode.WEB_FALLBACK


def test_agentic_router_sufficient_context_internal_only(agentic_router: AgenticRouter):
    high_score_chunks = [
        RetrievedChunk(
            chunk_id="c_high",
            document_id="d1",
            workspace_id="w1",
            score=0.88,  # above 0.30 threshold
            text="The activation energy was determined to be 18.4 kcal/mol.",
            page_number=4,
        )
    ]
    decision = agentic_router.evaluate(
        query="What is the activation energy of the catalyst?",
        retrieved_chunks=high_score_chunks,
    )
    assert decision.should_use_web is False
    assert decision.mode == RoutingMode.INTERNAL_ONLY


def test_llm_gateway_provider_management():
    gateway = LLMGateway()
    gateway.register_llm_provider(MockLLMProvider())

    # Switch active provider
    gateway.set_active_llm_provider("mock")
    assert gateway._active_llm_provider_name == "mock"

    # Switching to unregistered provider must raise ValueError
    with pytest.raises(ValueError) as exc:
        gateway.set_active_llm_provider("non_existent_provider_xyz")
    assert "not registered" in str(exc.value)


@pytest.mark.asyncio
async def test_agentic_rag_engine_execution(mock_agentic_engine: AgenticRAGEngine):
    req = RAGRequest(
        query_text="What does NMR show for compound 4a?",
        workspace_id="ws1",
        model="mock",
    )
    resp = await mock_agentic_engine.execute(req)
    assert len(resp.answer) > 0
    assert resp.workspace_id == "ws1"
    assert isinstance(resp.citations, list)


@pytest.mark.asyncio
async def test_agentic_rag_engine_streaming(mock_agentic_engine: AgenticRAGEngine):
    req = RAGRequest(
        query_text="Describe NMR peaks",
        workspace_id="ws1",
        model="mock",
    )
    chunks_received = []
    async for chunk in mock_agentic_engine.stream_execute(req):
        chunks_received.append(chunk)

    assert len(chunks_received) > 0
    # Final chunk should contain stop finish_reason
    stop_chunk = chunks_received[-1]
    assert stop_chunk.get("finish_reason") == "stop"
    assert "citations" in stop_chunk
