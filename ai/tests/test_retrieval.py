import asyncio
import unittest
from ai.embeddings.pipeline import EmbeddingPipeline
from ai.generation.gateway import LLMGateway
from ai.providers.mock_llm import MockLLMProvider
from ai.providers.ollama_embedding import MockEmbeddingProvider
from ai.retrieval.dense import DenseRetriever
from ai.schemas.document import DocumentChunk
from ai.schemas.retrieval import RetrievalQuery
from ai.vector_store.mock_store import MockVectorStore

class TestDenseRetriever(unittest.TestCase):

    def setUp(self):
        self.gateway = LLMGateway()
        self.gateway.register_llm_provider(MockLLMProvider())
        self.gateway.register_embedding_provider(MockEmbeddingProvider())
        self.gateway.set_active_llm_provider("mock")
        self.gateway.set_active_embedding_provider("mock")

        self.store = MockVectorStore()
        self.pipeline = EmbeddingPipeline(vector_store=self.store, llm_gateway=self.gateway)
        self.retriever = DenseRetriever(vector_store=self.store, llm_gateway=self.gateway)

    def test_dense_retrieval_workspace_isolation_and_filtering(self):
        async def run_test():
            collection = "chem_papers"

            # Index chunks for Workspace 1
            chunks_ws1 = [
                DocumentChunk(
                    chunk_id="chunk_ws1_a",
                    document_id="doc_1",
                    workspace_id="ws_1",
                    text="Synthesis of Aspirin in THF solvent with H2SO4 catalyst.",
                    page_number=1,
                    section_title="Methods",
                    chemical_entities=["THF", "H2SO4", "Aspirin"]
                ),
                DocumentChunk(
                    chunk_id="chunk_ws1_b",
                    document_id="doc_1",
                    workspace_id="ws_1",
                    text="NMR spectra analysis in CDCl3.",
                    page_number=2,
                    section_title="Results",
                    chemical_entities=["CDCl3"]
                ),
            ]

            # Index chunks for Workspace 2
            chunks_ws2 = [
                DocumentChunk(
                    chunk_id="chunk_ws2_a",
                    document_id="doc_99",
                    workspace_id="ws_2",
                    text="Organic solar cells with fullerene derivatives.",
                    page_number=1,
                    section_title="Introduction",
                    chemical_entities=["Fullerene"]
                ),
            ]

            await self.pipeline.embed_and_index_chunks(collection, chunks_ws1)
            await self.pipeline.embed_and_index_chunks(collection, chunks_ws2)

            # 1. Query for ws_1 -> MUST NOT return ws_2 chunks
            query_ws1 = RetrievalQuery(
                query_text="THF solvent synthesis",
                workspace_id="ws_1",
                collection_name=collection,
                top_k=5
            )
            response_ws1 = await self.retriever.retrieve(query_ws1)

            self.assertEqual(len(response_ws1.results), 2)
            for item in response_ws1.results:
                self.assertEqual(item.workspace_id, "ws_1")

            # 2. Query with chemical_filter requiring CDCl3
            query_chem = RetrievalQuery(
                query_text="NMR spectra",
                workspace_id="ws_1",
                collection_name=collection,
                chemical_filter=["CDCl3"]
            )
            response_chem = await self.retriever.retrieve(query_chem)

            self.assertEqual(len(response_chem.results), 1)
            self.assertEqual(response_chem.results[0].chunk_id, "chunk_ws1_b")

            # 3. Query for ws_2 -> MUST return only ws_2 chunk
            query_ws2 = RetrievalQuery(
                query_text="solar cells",
                workspace_id="ws_2",
                collection_name=collection
            )
            response_ws2 = await self.retriever.retrieve(query_ws2)

            self.assertEqual(len(response_ws2.results), 1)
            self.assertEqual(response_ws2.results[0].workspace_id, "ws_2")
            self.assertEqual(response_ws2.results[0].chunk_id, "chunk_ws2_a")

        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()
