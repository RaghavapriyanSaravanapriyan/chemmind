import asyncio
import unittest
from ai.embeddings.pipeline import EmbeddingPipeline
from ai.generation.gateway import LLMGateway
from ai.providers.mock_llm import MockLLMProvider
from ai.providers.ollama_embedding import MockEmbeddingProvider
from ai.schemas.document import DocumentChunk
from ai.vector_store.mock_store import MockVectorStore

class TestEmbeddingPipeline(unittest.TestCase):

    def test_pipeline_embed_and_index(self):
        async def run_test():
            # Setup gateway with Mock providers
            gateway = LLMGateway()
            gateway.register_llm_provider(MockLLMProvider())
            gateway.register_embedding_provider(MockEmbeddingProvider())
            gateway.set_active_llm_provider("mock")
            gateway.set_active_embedding_provider("mock")

            store = MockVectorStore()
            pipeline = EmbeddingPipeline(vector_store=store, llm_gateway=gateway)

            chunks = [
                DocumentChunk(
                    chunk_id="c_1",
                    document_id="doc_10",
                    workspace_id="ws_main",
                    text="Paragraph on synthesis of aspirin in EtOH.",
                    page_number=1,
                    section_title="1. Introduction",
                    chunk_type="text",
                    chemical_entities=["EtOH"]
                ),
                DocumentChunk(
                    chunk_id="c_2",
                    document_id="doc_10",
                    workspace_id="ws_main",
                    text="\\begin{equation}\n\\Delta G = \\Delta H - T\\Delta S\n\\end{equation}",
                    page_number=2,
                    section_title="2. Thermodynamics",
                    chunk_type="equation",
                    chemical_entities=[]
                ),
            ]

            total_indexed = await pipeline.embed_and_index_chunks(
                collection_name="chem_papers",
                chunks=chunks
            )

            self.assertEqual(total_indexed, 2)

            # Perform search to verify vector store received the points and payloads
            query_vector = [0.1] * 384
            search_res = await store.search(
                collection_name="chem_papers",
                query_vector=query_vector,
                limit=10,
                workspace_id="ws_main"
            )

            self.assertEqual(len(search_res), 2)
            chunk_ids = {r.chunk_id for r in search_res}
            self.assertIn("c_1", chunk_ids)
            self.assertIn("c_2", chunk_ids)

        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()
