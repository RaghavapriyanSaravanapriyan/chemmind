from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CitationBase(BaseModel):
    document_id: str | None = None
    page: int | None = None
    chunk_id: str | None = None
    section: str | None = None
    excerpt: str | None = None
    source_type: str = "document"
    url: str | None = None
    title: str | None = None
    domain: str | None = None



class CitationCreate(CitationBase):
    pass


class CitationRead(CitationBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    message_id: str
    created_at: datetime


class MessageCreate(BaseModel):
    sender: str  # user or assistant
    content: str
    citations: list[CitationCreate] = []


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    sender: str
    content: str
    created_at: datetime
    citations: list[CitationRead] = []


class ConversationBase(BaseModel):
    title: str = "New Conversation"


class ConversationCreate(ConversationBase):
    pass


class ConversationUpdate(BaseModel):
    title: str | None = None


class ConversationRead(ConversationBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageRead] = []
