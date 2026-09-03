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
    default_llm_model: str = Field(default="qwen2.5:1.5b", description="Default LLM model name")
    default_embedding_model: str = Field(default="hf.co/CompendiumLabs/bge-base-en-v1.5-gguf:latest", description="Default embedding model name")

    # Cloud API settings (OpenAI, OpenRouter, Groq, Gemini, Anthropic)
    openai_api_key: Optional[str] = Field(default=None, description="API key for OpenAI / OpenRouter / Groq endpoints")
    openai_base_url: str = Field(default="https://api.openai.com/v1", description="Base URL for OpenAI-compatible cloud API")
    openai_default_model: str = Field(default="gpt-4o-mini", description="Default OpenAI LLM model")
    openai_default_embedding_model: str = Field(default="text-embedding-3-small", description="Default OpenAI embedding model")
    anthropic_api_key: Optional[str] = Field(default=None, description="API key for Anthropic Claude endpoints")
    gemini_api_key: Optional[str] = Field(default=None, description="API key for Google Gemini endpoints")

    # Vector DB (Qdrant) settings
    qdrant_host: str = Field(default="localhost", description="Qdrant host")
    qdrant_port: int = Field(default=6333, description="Qdrant port")
    qdrant_url: Optional[str] = Field(default=None, description="Full Qdrant URL override (takes precedence over host/port)")
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

    def model_post_init(self, __context=None) -> None:
        # Compatibility: also honour single-prefix Rust-style vars
        # (CHEMMIND_OLLAMA_BASE_URL, CHEMMIND_DEFAULT_LLM_MODEL, ...) when the
        # doubled CHEMMIND_AI_* variants are not set. This keeps docker-compose
        # (which sets CHEMMIND_*) working for the Python subsystem.
        legacy_map = {
            "ollama_base_url": "CHEMMIND_OLLAMA_BASE_URL",
            "default_llm_model": "CHEMMIND_DEFAULT_LLM_MODEL",
            "default_embedding_model": "CHEMMIND_DEFAULT_EMBEDDING_MODEL",
            "qdrant_host": "CHEMMIND_AI_QDRANT_HOST",
            "openai_api_key": "OPENAI_API_KEY",
            "openai_base_url": "OPENAI_BASE_URL",
            "anthropic_api_key": "ANTHROPIC_API_KEY",
            "gemini_api_key": "GEMINI_API_KEY",
        }
        # Single-prefix Qdrant overrides used by docker-compose / Rust.
        legacy_map.update({
            "qdrant_host": "CHEMMIND_QDRANT_HOST",
            "qdrant_url": "CHEMMIND_QDRANT_URL",
        })
        for field, legacy_key in legacy_map.items():
            prefixed_key = f"CHEMMIND_AI_{field.upper()}"
            if prefixed_key not in os.environ and legacy_key in os.environ:
                try:
                    object.__setattr__(self, field, os.environ[legacy_key])
                except Exception:
                    pass
        # QDRANT_HOST / QDRANT_PORT bare fallbacks (common in compose files).
        if "CHEMMIND_AI_QDRANT_HOST" not in os.environ and "QDRANT_HOST" in os.environ:
            try:
                object.__setattr__(self, "qdrant_host", os.environ["QDRANT_HOST"])
            except Exception:
                pass

    def qdrant_url_or_default(self) -> Optional[str]:
        """Returns explicit qdrant_url override if configured."""
        return self.qdrant_url

# Singleton instance
settings = AISettings()
