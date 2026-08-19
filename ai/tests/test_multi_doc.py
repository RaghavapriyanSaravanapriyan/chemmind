import asyncio
import unittest
from ai.embeddings.pipeline import EmbeddingPipeline
from ai.generation.gateway import LLMGateway
from ai.providers.mock_llm import MockLLMProvider
from ai.providers.ollama_embedding import MockEmbeddingProvider
from ai.reasoning.multi_doc_engine import MultiDocReasoningEngine
from ai.retrieval.dense import DenseRetriever
from ai.schemas.document import DocumentChunk
from ai.schemas.reasoning import MultiDocAnalysisRequest
from ai.vector_store.mock_store import MockVectorStore

class TestMultiDocReasoning(unittest.TestCase):

    def test_multi_doc_cross_examination(self):
        async def run_test():
            gateway = LLMGateway()
            gateway.register_llm_provider(MockLLMProvider())
            gateway.register_embedding_provider(MockEmbeddingProvider())
            gateway.set_active_llm_provider("mock")
            gateway.set_active_embedding_provider("mock")

            store = MockVectorStore()
            pipeline = EmbeddingPipeline(vector_store=store, llm_gateway=gateway)
            retriever = DenseRetriever(vector_store=store, llm_gateway=gateway)
            engine = MultiDocReasoningEngine(retriever=retriever, llm_gateway=gateway)

            collection = "multi_doc_coll"
            chunks = [
                DocumentChunk(
                    chunk_id="chk_paper1",
                    document_id="paper_1",
                    workspace_id="ws_lab",
                    text="Paper 1 reports 85% yield of Compound X at 80 °C using Pd catalyst.",
                    page_number=3,
                    section_title="Results"
                ),
                DocumentChunk(
                    chunk_id="chk_paper2",
                    document_id="paper_2",
                    workspace_id="ws_lab",
                    text="Paper 2 reports 92% yield of Compound X at 120 °C using Ni catalyst.",
                    page_number=5,
                    section_title="Experimental"
                ),
            ]
            await pipeline.embed_and_index_chunks(collection, chunks)

            req = MultiDocAnalysisRequest(
                document_ids=["paper_1", "paper_2"],
                query_text="Compare the yields and catalysts reported for Compound X.",
                workspace_id="ws_lab",
                collection_name=collection
            )
            response = await engine.analyze(req)

            self.assertIsNotNone(response.summary)
            self.assertEqual(response.workspace_id, "ws_lab")
            self.assertEqual(len(response.comparison_matrix), 2)
            self.assertEqual(len(response.discrepancies), 1)

        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()
