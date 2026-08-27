import unittest
import asyncio
from ai.providers.mock_llm import MockLLMProvider
from ai.providers.ollama_embedding import MockEmbeddingProvider
from ai.schemas import ChatMessage, Role, LLMRequest, EmbeddingRequest

class TestProviders(unittest.TestCase):

    def test_mock_llm_generate(self):
        async def run_test():
            provider = MockLLMProvider(mock_response="Mocked response test.")
            req = LLMRequest(messages=[ChatMessage(role=Role.USER, content="Test prompt")])
            response = await provider.generate(req)
            self.assertEqual(response.content, "Mocked response test.")
            self.assertEqual(provider.provider_name, "mock")

        asyncio.run(run_test())

    def test_mock_llm_stream(self):
        async def run_test():
            provider = MockLLMProvider(mock_response="Hello world")
            req = LLMRequest(messages=[ChatMessage(role=Role.USER, content="Test")])
            chunks = []
            async for chunk in provider.stream(req):
                chunks.append(chunk.delta_content)
            self.assertEqual("".join(chunks), "Hello world")

        asyncio.run(run_test())

    def test_mock_embedding(self):
        async def run_test():
            provider = MockEmbeddingProvider(vector_dim=128)
            req = EmbeddingRequest(input_texts=["Chemistry paper text"])
            response = await provider.embed(req)
            self.assertEqual(len(response.embeddings), 1)
            self.assertEqual(len(response.embeddings[0]), 128)

        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()
