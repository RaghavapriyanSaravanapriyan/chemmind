import asyncio
import unittest
from ai.embeddings.pipeline import EmbeddingPipeline
from ai.generation.gateway import LLMGateway
from ai.providers.mock_llm import MockLLMProvider
from ai.providers.ollama_embedding import MockEmbeddingProvider
from ai.retrieval.dense import DenseRetriever
from ai.retrieval.hybrid import HybridRetriever
from ai.retrieval.rrf import reciprocal_rank_fusion
from ai.retrieval.sparse import BM25KeywordRetriever, tokenize_chemistry_text
from ai.schemas.document import DocumentChunk
from ai.schemas.retrieval import RetrievalQuery, RetrievedChunk
from ai.vector_store.mock_store import MockVectorStore

class TestHybridRetrieval(unittest.TestCase):

    def test_chemistry_tokenization(self):
        text = "Reaction in THF using Pd(PPh3)4 catalyst."
        tokens = tokenize_chemistry_text(text)
        self.assertIn("THF", tokens)
        self.assertIn("Pd(PPh3)4", tokens)
        self.assertIn("reaction", tokens)

    def test_bm25_sparse_keyword_ranking(self):
        bm25 = BM25KeywordRetriever()
        chunks = [
            DocumentChunk(
                chunk_id="chunk_a",
                document_id="doc_1",
                workspace_id="ws_1",
                text="The catalyst Pd(PPh3)4 was added in 5 mol% quantity.",
                page_number=1,
                chemical_entities=["Pd(PPh3)4"]
            ),
            DocumentChunk(
                chunk_id="chunk_b",
                document_id="doc_1",
                workspace_id="ws_1",
                text="General introduction to organic synthesis without specific catalysts.",
                page_number=2,
                chemical_entities=[]
            ),
        ]
        results = bm25.rank_chunks("Pd(PPh3)4 catalyst", chunks)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].chunk_id, "chunk_a")

    def test_reciprocal_rank_fusion(self):
        c1 = RetrievedChunk(chunk_id="chunk_1", score=0.9, text="t1", document_id="d1", workspace_id="ws1", page_number=1)
        c2 = RetrievedChunk(chunk_id="chunk_2", score=0.8, text="t2", document_id="d1", workspace_id="ws1", page_number=1)
        c3 = RetrievedChunk(chunk_id="chunk_3", score=0.7, text="t3", document_id="d1", workspace_id="ws1", page_number=1)

        dense = [c1, c2]
        sparse = [c2, c3]

        fused = reciprocal_rank_fusion(dense, sparse, k=60)
        
        # c2 appears in both dense and sparse, so its RRF score should be highest!
        self.assertEqual(fused[0].chunk_id, "chunk_2")

    def test_hybrid_retriever_end_to_end(self):
        async def run_test():
            gateway = LLMGateway()
            gateway.register_llm_provider(MockLLMProvider())
            gateway.register_embedding_provider(MockEmbeddingProvider())
            gateway.set_active_llm_provider("mock")
            gateway.set_active_embedding_provider("mock")

            store = MockVectorStore()
            pipeline = EmbeddingPipeline(vector_store=store, llm_gateway=gateway)
            dense_retriever = DenseRetriever(vector_store=store, llm_gateway=gateway)
            hybrid_retriever = HybridRetriever(dense_retriever=dense_retriever)

            collection = "chem_hybrid_test"
            chunks = [
                DocumentChunk(
                    chunk_id="chk_1",
                    document_id="doc_x",
                    workspace_id="ws_lab",
                    text="Synthesis of Aspirin with H2SO4 acid catalyst.",
                    page_number=1,
                    chemical_entities=["H2SO4", "Aspirin"]
                ),
                DocumentChunk(
                    chunk_id="chk_2",
                    document_id="doc_x",
                    workspace_id="ws_lab",
                    text="Thermodynamics of gas expansion in vacuum.",
                    page_number=4,
                    chemical_entities=[]
                ),
            ]

            await pipeline.embed_and_index_chunks(collection, chunks)

            query = RetrievalQuery(
                query_text="Aspirin synthesis H2SO4",
                workspace_id="ws_lab",
                collection_name=collection
            )

            resp = await hybrid_retriever.retrieve(query, candidate_chunks=chunks)

            self.assertTrue(len(resp.results) > 0)
            self.assertEqual(resp.results[0].chunk_id, "chk_1")

        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()
