from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

class ChatMessage(BaseModel):
    role: Role
    content: str
    name: Optional[str] = None

class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class LLMRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    max_tokens: Optional[int] = None
    stream: bool = False
    system_prompt: Optional[str] = None
    options: Dict[str, Any] = Field(default_factory=dict)

class LLMResponse(BaseModel):
    content: str
    model: str
    finish_reason: Optional[str] = "stop"
    usage: TokenUsage = Field(default_factory=TokenUsage)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class StreamChunk(BaseModel):
    delta_content: str
    finish_reason: Optional[str] = None
    model: Optional[str] = None
    is_final: bool = False
