import unittest
from ai.generation.gateway import LLMGateway
from ai.providers.openai_provider import OpenAILLMProvider, OpenAIEmbeddingProvider

class TestOpenAICloudProviders(unittest.TestCase):

    def test_openai_llm_provider_init(self):
        provider = OpenAILLMProvider(api_key="sk-test-key-12345", base_url="https://api.openai.com/v1")
        self.assertEqual(provider.provider_name, "openai")
        self.assertEqual(provider.api_key, "sk-test-key-12345")
        self.assertEqual(provider.base_url, "https://api.openai.com/v1")

    def test_openai_embedding_provider_init(self):
        provider = OpenAIEmbeddingProvider(api_key="sk-test-key-12345", base_url="https://api.openai.com/v1")
        self.assertEqual(provider.provider_name, "openai")
        self.assertEqual(provider.api_key, "sk-test-key-12345")

    def test_gateway_registration_and_switching(self):
        gateway = LLMGateway()
        
        # Switch to OpenAI providers
        gateway.set_active_llm_provider("openai")
        gateway.set_active_embedding_provider("openai")

        self.assertEqual(gateway.get_llm_provider().provider_name, "openai")
        self.assertEqual(gateway.get_embedding_provider().provider_name, "openai")

        # Switch back to Mock
        gateway.set_active_llm_provider("mock")
        gateway.set_active_embedding_provider("mock")

        self.assertEqual(gateway.get_llm_provider().provider_name, "mock")
        self.assertEqual(gateway.get_embedding_provider().provider_name, "mock")

if __name__ == "__main__":
    unittest.main()
