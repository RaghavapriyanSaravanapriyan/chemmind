import pytest
from ai.generation.gateway import LLMGateway
from ai.providers.mock_llm import MockLLMProvider
from ai.providers.ollama_embedding import MockEmbeddingProvider
from ai.retrieval.dense import DenseRetriever
from ai.retrieval.hybrid import HybridRetriever
from ai.retrieval.rrf import reciprocal_rank_fusion
from ai.retrieval.sparse import BM25KeywordRetriever
from ai.schemas.document import DocumentChunk
from ai.schemas.retrieval import RetrievalQuery, RetrievedChunk
from ai.schemas.vector import VectorPoint
from ai.vector_store.mock_store import MockVectorStore


def create_mock_gateway():
    return LLMGateway(
        llm_provider=MockLLMProvider(),
        embedding_provider=MockEmbeddingProvider(vector_dim=384),
    )


async def create_populated_vector_store():
    store = MockVectorStore()
    points = [
        VectorPoint(
            id="chunk_1",
            vector=[0.1] * 384,
            payload={
                "text": "High efficiency palladium catalyzed Suzuki cross-coupling reaction in water.",
                "workspace_id": "ws_001",
                "document_id": "doc_001",
                "page_number": 1,
                "section_title": "Catalysis",
                "chemical_entities": ["Pd", "H2O"],
                "chunk_type": "text",
                "page_start": 1,
                "page_end": 1,
            },
        ),
        VectorPoint(
            id="chunk_2",
            vector=[0.05] * 384,
            payload={
                "text": "Enantioselective hydrogenation using chiral ruthenium BINAP complexes.",
                "workspace_id": "ws_001",
                "document_id": "doc_001",
                "page_number": 3,
                "section_title": "Hydrogenation",
                "chemical_entities": ["Ru", "BINAP"],
                "chunk_type": "text",
                "page_start": 3,
                "page_end": 3,
            },
        ),
        VectorPoint(
            id="chunk_3",
            vector=[0.1] * 384,
            payload={
                "text": "Foreign workspace document that must not be leaked.",
                "workspace_id": "ws_foreign",
                "document_id": "doc_foreign",
                "page_number": 1,
                "section_title": "Secret",
                "chemical_entities": [],
                "chunk_type": "text",
                "page_start": 1,
                "page_end": 1,
            },
        ),
    ]
    await store.upsert_points("chemmind_chunks", points)
    return store


@pytest.mark.asyncio
async def test_dense_retrieval_workspace_isolation():
    gateway = create_mock_gateway()
    vstore = await create_populated_vector_store()
    retriever = DenseRetriever(vector_store=vstore, llm_gateway=gateway)

    query = RetrievalQuery(
        query_text="palladium catalysis",
        workspace_id="ws_001",
        top_k=5,
    )
    resp = await retriever.retrieve(query)

    assert resp.total_retrieved >= 1
    # Ensure no foreign workspace leakage
    for r in resp.results:
        assert r.workspace_id == "ws_001"
        assert r.document_id != "doc_foreign"


@pytest.mark.asyncio
async def test_dense_retrieval_chemical_filter():
    gateway = create_mock_gateway()
    vstore = await create_populated_vector_store()
    retriever = DenseRetriever(vector_store=vstore, llm_gateway=gateway)

    query = RetrievalQuery(
        query_text="catalytic reaction",
        workspace_id="ws_001",
        chemical_filter=["BINAP"],
        top_k=5,
    )
    resp = await retriever.retrieve(query)

    assert all("BINAP" in r.chemical_entities for r in resp.results)


def test_sparse_bm25_retriever():
    bm25 = BM25KeywordRetriever()
    chunks = [
        DocumentChunk(
            chunk_id="c1",
            document_id="d1",
            workspace_id="w1",
            text="Synthesis of ruthenium catalyst for asymmetric reduction.",
            page_number=1,
        ),
        DocumentChunk(
            chunk_id="c2",
            document_id="d1",
            workspace_id="w1",
            text="General laboratory safety equipment and fume hood maintenance.",
            page_number=2,
        ),
    ]

    ranked = bm25.rank_chunks("ruthenium asymmetric catalyst", chunks, top_k=2)
    assert len(ranked) >= 1
    assert ranked[0].chunk_id == "c1"


def test_reciprocal_rank_fusion_logic():
    dense_list = [
        RetrievedChunk(chunk_id="A", document_id="d1", workspace_id="w1", score=0.9, text="Text A", page_number=1),
        RetrievedChunk(chunk_id="B", document_id="d1", workspace_id="w1", score=0.8, text="Text B", page_number=2),
    ]
    sparse_list = [
        RetrievedChunk(chunk_id="B", document_id="d1", workspace_id="w1", score=0.95, text="Text B", page_number=2),
        RetrievedChunk(chunk_id="C", document_id="d1", workspace_id="w1", score=0.7, text="Text C", page_number=3),
    ]

    fused = reciprocal_rank_fusion(dense_list, sparse_list, k=60)
    assert len(fused) == 3
    # Item B appeared in both lists, so its fused score should place it at the top
    assert fused[0].chunk_id == "B"


@pytest.mark.asyncio
async def test_hybrid_retriever_end_to_end():
    gateway = create_mock_gateway()
    vstore = await create_populated_vector_store()
    dense_retriever = DenseRetriever(vector_store=vstore, llm_gateway=gateway)
    hybrid_retriever = HybridRetriever(dense_retriever=dense_retriever)

    query = RetrievalQuery(
        query_text="palladium suzuki cross-coupling",
        workspace_id="ws_001",
        top_k=2,
    )
    resp = await hybrid_retriever.retrieve(query)
    assert resp.total_retrieved >= 1
    assert any("palladium" in r.text.lower() for r in resp.results)
