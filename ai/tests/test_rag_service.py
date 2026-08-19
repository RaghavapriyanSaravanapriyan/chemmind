import asyncio
import unittest
from ai.embeddings.pipeline import EmbeddingPipeline
from ai.generation.gateway import LLMGateway
from ai.generation.rag_service import RAGGenerationService
from ai.prompts.chem_rag_prompt import build_rag_prompt, CHEMISTRY_RAG_SYSTEM_PROMPT
from ai.providers.mock_llm import MockLLMProvider
from ai.providers.ollama_embedding import MockEmbeddingProvider
from ai.retrieval.dense import DenseRetriever
from ai.schemas.document import DocumentChunk
from ai.schemas.rag import RAGRequest
from ai.schemas.retrieval import RetrievedChunk
from ai.vector_store.mock_store import MockVectorStore

class TestRAGPromptsAndService(unittest.TestCase):

    def setUp(self):
        self.gateway = LLMGateway()
        self.gateway.register_llm_provider(MockLLMProvider())
        self.gateway.register_embedding_provider(MockEmbeddingProvider())
        self.gateway.set_active_llm_provider("mock")
        self.gateway.set_active_embedding_provider("mock")

        self.store = MockVectorStore()
        self.pipeline = EmbeddingPipeline(vector_store=self.store, llm_gateway=self.gateway)
        self.retriever = DenseRetriever(vector_store=self.store, llm_gateway=self.gateway)
        self.rag_service = RAGGenerationService(retriever=self.retriever, llm_gateway=self.gateway)

    def test_build_rag_prompt_formatting(self):
        ret_chunks = [
            RetrievedChunk(
                chunk_id="chunk_1",
                score=0.92,
                text="Benzene reacts with HNO3 in H2SO4 to form Nitrobenzene.",
                document_id="doc_chem",
                workspace_id="ws_1",
                page_number=3,
                section_title="Synthesis",
                chemical_entities=["Benzene", "HNO3", "H2SO4"]
            )
        ]
        messages = build_rag_prompt("What is the synthesis of Nitrobenzene?", ret_chunks)

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].content, CHEMISTRY_RAG_SYSTEM_PROMPT)
        self.assertIn("EVIDENCE BLOCK [1]", messages[1].content)
        self.assertIn("Benzene reacts with HNO3", messages[1].content)
        self.assertIn("What is the synthesis of Nitrobenzene?", messages[1].content)

    def test_rag_generation_sync_and_stream(self):
        async def run_test():
            collection = "chem_papers"

            # Index evidence chunk into store
            chunks = [
                DocumentChunk(
                    chunk_id="c_synth",
                    document_id="paper_99",
                    workspace_id="ws_lab",
                    text="The activation energy Ea was calculated to be 52.4 kJ/mol in THF.",
                    page_number=5,
                    section_title="Kinetics",
                    chemical_entities=["THF"]
                )
            ]
            await self.pipeline.embed_and_index_chunks(collection, chunks)

            # Test synchronous RAG answer generation
            req = RAGRequest(
                query_text="What is the activation energy?",
                workspace_id="ws_lab",
                collection_name=collection
            )
            response = await self.rag_service.generate(req)

            self.assertIsNotNone(response.answer)
            self.assertEqual(response.workspace_id, "ws_lab")
            self.assertEqual(len(response.retrieved_chunks), 1)
            self.assertEqual(response.retrieved_chunks[0].chunk_id, "c_synth")

            # Test streaming RAG answer generation
            tokens = []
            async for token in self.rag_service.stream(req):
                tokens.append(token)

            full_streamed_answer = "".join(tokens)
            self.assertTrue(len(full_streamed_answer) > 0)

        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()
