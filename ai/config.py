import os
from typing import Optional
from pydantic import Field
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    from pydantic import BaseModel as BaseSettings  # type: ignore

class AISettings(BaseSettings):
    """Configuration settings for the ChemMind AI/RAG subsystem."""

    # Provider settings
    ai_provider: str = Field(default="ollama", description="Active LLM provider ('ollama', 'openai', 'mock')")
    embedding_provider: str = Field(default="ollama", description="Active Embedding provider ('ollama', 'openai', 'mock')")

    # Ollama local settings
    ollama_base_url: str = Field(default="http://localhost:11434", description="Base URL for local Ollama service")
    default_llm_model: str = Field(default="llama3", description="Default LLM model name")
    default_embedding_model: str = Field(default="nomic-embed-text", description="Default embedding model name")

    # Cloud API settings (OpenAI, OpenRouter, Groq, Gemini, Anthropic)
    openai_api_key: Optional[str] = Field(default=None, description="API key for OpenAI / OpenRouter / Groq endpoints")
    openai_base_url: str = Field(default="https://api.openai.com/v1", description="Base URL for OpenAI-compatible cloud API")
    anthropic_api_key: Optional[str] = Field(default=None, description="API key for Anthropic Claude endpoints")
    gemini_api_key: Optional[str] = Field(default=None, description="API key for Google Gemini endpoints")

    # Vector DB (Qdrant) settings
    qdrant_host: str = Field(default="localhost", description="Qdrant host")
    qdrant_port: int = Field(default=6333, description="Qdrant port")
    qdrant_collection_name: str = Field(default="chemmind_chunks", description="Qdrant collection name")

    # Logging
    log_level: str = Field(default="INFO", description="Log level for AI package")

    # Timeouts & Retries
    httpx_timeout_seconds: float = Field(default=60.0, description="HTTP request timeout in seconds")

    model_config = {
        "env_prefix": "CHEMMIND_AI_",
        "case_sensitive": False,
        "extra": "ignore"
    }

# Singleton instance
settings = AISettings()
