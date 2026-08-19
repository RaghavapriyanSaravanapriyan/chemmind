from typing import List, Optional
from pydantic import BaseModel, Field
from ai.schemas.llm import TokenUsage
from ai.schemas.retrieval import RetrievedChunk

class RAGRequest(BaseModel):
    query_text: str = Field(..., description="User question or chemistry query")
    workspace_id: str = Field(..., description="Target workspace ID")
    collection_name: str = Field(default="chem_papers", description="Vector store collection name")
    document_ids: Optional[List[str]] = Field(default=None, description="Optional list of document IDs to restrict retrieval")
    top_k: int = Field(default=5, ge=1, le=50, description="Max candidate evidence chunks to retrieve")
    min_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Similarity score cutoff threshold")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0, description="LLM sampling temperature")
    model: Optional[str] = Field(default=None, description="Optional LLM model override")
    stream: bool = Field(default=False, description="Enable streaming token output")

class RAGResponse(BaseModel):
    answer: str = Field(..., description="Generated answer text")
    retrieved_chunks: List[RetrievedChunk] = Field(default_factory=list, description="Retrieved candidate evidence chunks used")
    usage: Optional[TokenUsage] = Field(default=None, description="Token consumption metrics")
    model: str = Field(..., description="LLM model used for generation")
    workspace_id: str = Field(..., description="Workspace ID")
