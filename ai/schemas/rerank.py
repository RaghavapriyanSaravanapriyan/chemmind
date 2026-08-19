from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from ai.schemas.retrieval import RetrievedChunk

class RerankRequest(BaseModel):
    query_text: str = Field(..., description="User query text")
    candidate_chunks: List[RetrievedChunk] = Field(..., description="List of candidate chunks to re-score and re-rank")
    top_k: int = Field(default=5, ge=1, le=50, description="Max candidate chunks to return after reranking")
    min_relevance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum rerank score threshold cutoff")

class RerankedChunk(BaseModel):
    chunk_id: str
    rerank_score: float = Field(..., description="Refined reranking relevance score [0.0 - 1.0]")
    original_score: float = Field(..., description="Original vector or hybrid similarity score")
    text: str
    document_id: str
    workspace_id: str
    page_number: int
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    section_title: Optional[str] = None
    chemical_entities: List[str] = Field(default_factory=list)
    chunk_type: str = Field(default="text")
    payload: Dict[str, Any] = Field(default_factory=dict)

class RerankResponse(BaseModel):
    query_text: str
    results: List[RerankedChunk] = Field(default_factory=list)
    total_reranked: int = 0
