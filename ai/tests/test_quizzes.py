import asyncio
import unittest
from ai.embeddings.pipeline import EmbeddingPipeline
from ai.generation.gateway import LLMGateway
from ai.providers.mock_llm import MockLLMProvider
from ai.providers.ollama_embedding import MockEmbeddingProvider
from ai.quizzes.generator import QuizGenerator
from ai.retrieval.dense import DenseRetriever
from ai.schemas.document import DocumentChunk
from ai.schemas.quiz import QuizGenerationRequest, QuizType
from ai.vector_store.mock_store import MockVectorStore

class TestGroundedQuizzes(unittest.TestCase):

    def test_quiz_generation(self):
        async def run_test():
            gateway = LLMGateway()
            gateway.register_llm_provider(MockLLMProvider())
            gateway.register_embedding_provider(MockEmbeddingProvider())
            gateway.set_active_llm_provider("mock")
            gateway.set_active_embedding_provider("mock")

            store = MockVectorStore()
            pipeline = EmbeddingPipeline(vector_store=store, llm_gateway=gateway)
            retriever = DenseRetriever(vector_store=store, llm_gateway=gateway)
            quiz_gen = QuizGenerator(retriever=retriever, llm_gateway=gateway)

            collection = "quiz_test_coll"
            chunks = [
                DocumentChunk(
                    chunk_id="chk_q1",
                    document_id="paper_100",
                    workspace_id="ws_class",
                    text="Synthesis of Acetaminophen requires p-aminophenol and acetic anhydride in water at 60 °C.",
                    page_number=2,
                    section_title="Methods"
                )
            ]
            await pipeline.embed_and_index_chunks(collection, chunks)

            req = QuizGenerationRequest(
                workspace_id="ws_class",
                num_questions=1,
                quiz_type=QuizType.MULTIPLE_CHOICE,
                topic="Acetaminophen Synthesis",
                collection_name=collection
            )
            response = await quiz_gen.generate_quiz(req)

            self.assertEqual(response.workspace_id, "ws_class")
            self.assertEqual(len(response.questions), 1)
            q = response.questions[0]
            self.assertEqual(len(q.options), 4)
            self.assertEqual(q.correct_answer, "A")
            self.assertTrue(len(q.citations) > 0)

        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()
