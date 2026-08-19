import asyncio
import unittest
from ai.embeddings.pipeline import EmbeddingPipeline
from ai.generation.gateway import LLMGateway
from ai.generation.rag_service import RAGGenerationService
from ai.providers.mock_llm import MockLLMProvider
from ai.providers.ollama_embedding import MockEmbeddingProvider
from ai.reranking.cross_encoder import ChemistryCrossEncoderReranker
from ai.retrieval.dense import DenseRetriever
from ai.schemas.document import DocumentChunk
from ai.schemas.rag import RAGRequest
from ai.schemas.rerank import RerankRequest
from ai.schemas.retrieval import RetrievedChunk
from ai.vector_store.mock_store import MockVectorStore

class TestRerankingEngine(unittest.TestCase):

    def setUp(self):
        self.reranker = ChemistryCrossEncoderReranker()

    def test_reranker_reordering_and_boosts(self):
        async def run_test():
            candidates = [
                RetrievedChunk(
                    chunk_id="chunk_generic",
                    score=0.90,  # Higher vector score initially
                    text="General discussion on synthetic organic transformations.",
                    document_id="doc_1",
                    workspace_id="ws_1",
                    page_number=1,
                    section_title="Introduction",
                    chemical_entities=[]
                ),
                RetrievedChunk(
                    chunk_id="chunk_chem_specific",
                    score=0.75,  # Lower vector score initially
                    text="The catalyst Pd(PPh3)4 in THF yielded 95% product.",
                    document_id="doc_1",
                    workspace_id="ws_1",
                    page_number=3,
                    section_title="Experimental Methods",
                    chemical_entities=["Pd(PPh3)4", "THF"]
                ),
            ]

            req = RerankRequest(
                query_text="What catalyst was used in Experimental Methods for THF?",
                candidate_chunks=candidates,
                top_k=2
            )
            response = await self.reranker.rerank(req)

            self.assertEqual(len(response.results), 2)
            # chunk_chem_specific should be promoted to #1 position due to chemical match and section boost!
            self.assertEqual(response.results[0].chunk_id, "chunk_chem_specific")
            self.assertTrue(response.results[0].rerank_score > response.results[1].rerank_score)

        asyncio.run(run_test())

    def test_rag_service_with_reranker(self):
        async def run_test():
            gateway = LLMGateway()
            gateway.register_llm_provider(MockLLMProvider())
            gateway.register_embedding_provider(MockEmbeddingProvider())
            gateway.set_active_llm_provider("mock")
            gateway.set_active_embedding_provider("mock")

            store = MockVectorStore()
            pipeline = EmbeddingPipeline(vector_store=store, llm_gateway=gateway)
            dense_retriever = DenseRetriever(vector_store=store, llm_gateway=gateway)
            rag_service = RAGGenerationService(
                retriever=dense_retriever,
                llm_gateway=gateway,
                reranker=self.reranker
            )

            collection = "rerank_test_coll"
            chunks = [
                DocumentChunk(
                    chunk_id="c_synth",
                    document_id="paper_10",
                    workspace_id="ws_lab",
                    text="Synthesis of Compound 3b in THF solvent.",
                    page_number=2,
                    section_title="Synthesis",
                    chemical_entities=["THF"]
                )
            ]
            await pipeline.embed_and_index_chunks(collection, chunks)

            req = RAGRequest(
                query_text="How was Compound 3b synthesized?",
                workspace_id="ws_lab",
                collection_name=collection
            )
            resp = await rag_service.generate(req)

            self.assertEqual(resp.workspace_id, "ws_lab")
            self.assertTrue(len(resp.retrieved_chunks) > 0)
            self.assertEqual(resp.retrieved_chunks[0].chunk_id, "c_synth")

        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()
