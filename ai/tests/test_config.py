import os
import unittest
from ai.config import AISettings

class TestConfig(unittest.TestCase):

    def test_default_settings(self):
        config = AISettings()
        self.assertEqual(config.ai_provider, "ollama")
        self.assertEqual(config.ollama_base_url, "http://localhost:11434")
        self.assertEqual(config.default_llm_model, "llama3")

    def test_env_override(self):
        os.environ["CHEMMIND_AI_AI_PROVIDER"] = "mock"
        os.environ["CHEMMIND_AI_DEFAULT_LLM_MODEL"] = "gemma2"
        try:
            config = AISettings()
            self.assertEqual(config.ai_provider, "mock")
            self.assertEqual(config.default_llm_model, "gemma2")
        finally:
            del os.environ["CHEMMIND_AI_AI_PROVIDER"]
            del os.environ["CHEMMIND_AI_DEFAULT_LLM_MODEL"]

if __name__ == "__main__":
    unittest.main()
