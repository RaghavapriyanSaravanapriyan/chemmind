from typing import List, Optional
from pydantic import BaseModel, Field

class EmbeddingRequest(BaseModel):
    input_texts: List[str] = Field(..., min_length=1)
    model: Optional[str] = None

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    model: str
    total_tokens: Optional[int] = None
    dimension: Optional[int] = None
