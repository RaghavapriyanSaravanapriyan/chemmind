import unittest
import asyncio
from ai.generation.gateway import LLMGateway
from ai.providers.mock_llm import MockLLMProvider
from ai.providers.ollama_embedding import MockEmbeddingProvider
from ai.schemas import ChatMessage, Role, LLMRequest, EmbeddingRequest

class TestGateway(unittest.TestCase):

    def test_gateway_with_mock_providers(self):
        async def run_test():
            mock_llm = MockLLMProvider("Gateway response")
            mock_emb = MockEmbeddingProvider(vector_dim=64)

            gateway = LLMGateway(llm_provider=mock_llm, embedding_provider=mock_emb)
            
            # Test generate
            req = LLMRequest(messages=[ChatMessage(role=Role.USER, content="Hello")])
            res = await gateway.generate(req)
            self.assertEqual(res.content, "Gateway response")

            # Test streaming
            stream_chunks = []
            async for chunk in gateway.stream(req):
                stream_chunks.append(chunk.delta_content)
            self.assertEqual("".join(stream_chunks), "Gateway response")

            # Test embed
            emb_req = EmbeddingRequest(input_texts=["Sample query"])
            emb_res = await gateway.embed(emb_req)
            self.assertEqual(len(emb_res.embeddings[0]), 64)

        asyncio.run(run_test())

    def test_provider_switching(self):
        gateway = LLMGateway()
        gateway.set_active_llm_provider("mock")
        self.assertEqual(gateway.get_llm_provider().provider_name, "mock")

        with self.assertRaises(ValueError):
            gateway.set_active_llm_provider("non_existent_provider")

if __name__ == "__main__":
    unittest.main()
