from pydantic import BaseModel
from app.schemas.conversation import CitationCreate, CitationRead


class AIChatRequest(BaseModel):
    prompt: str
    selected_document_ids: list[str] | None = None
    model_provider: str | None = "ollama"  # ollama, openai, mock


class AIChatResponse(BaseModel):
    message_id: str
    sender: str = "assistant"
    content: str
    citations: list[CitationRead] = []


class AIChatStreamChunk(BaseModel):
    token: str
    finish_reason: str | None = None
    citations: list[CitationCreate] | None = None
