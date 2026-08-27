from typing import List, Optional
from pydantic import BaseModel, Field
from ai.schemas.citation import Citation
from ai.schemas.llm import TokenUsage
from ai.schemas.retrieval import RetrievedChunk

class CitationMap(BaseModel):
    citations: List[Citation] = Field(default_factory=list, description="Resolved structured citation objects")
    cited_marker_indices: List[int] = Field(default_factory=list, description="List of 1-indexed evidence block numbers cited")
    unmapped_markers: List[int] = Field(default_factory=list, description="List of cited numbers that could not be mapped to chunks")

class CitedRAGResponse(BaseModel):
    answer: str = Field(..., description="Generated answer text with inline citation tags")
    citations: List[Citation] = Field(default_factory=list, description="Structured citation metadata mapped to source locations")
    retrieved_chunks: List[RetrievedChunk] = Field(default_factory=list, description="Raw retrieved evidence candidate chunks")
    usage: Optional[TokenUsage] = Field(default=None, description="LLM token consumption metrics")
    model: str = Field(..., description="LLM model used for generation")
    workspace_id: str = Field(..., description="Workspace ID")
