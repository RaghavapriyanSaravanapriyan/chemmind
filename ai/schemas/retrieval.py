from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class RetrievalQuery(BaseModel):
    query_text: str = Field(..., description="User question or query text")
    workspace_id: str = Field(..., description="Target workspace ID for strict boundary isolation")
    collection_name: str = Field(default="chem_papers", description="Target vector store collection name")
    document_ids: Optional[List[str]] = Field(default=None, description="Optional list of document IDs to restrict search")
    top_k: int = Field(default=5, ge=1, le=100, description="Max candidate chunks to retrieve")
    min_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum similarity score threshold cutoff")
    chemical_filter: Optional[List[str]] = Field(default=None, description="Optional list of chemical entities to require in results")

class RetrievedChunk(BaseModel):
    chunk_id: str
    score: float = Field(..., description="Cosine similarity score")
    text: str
    document_id: str
    workspace_id: str
    page_number: int = Field(..., description="1-indexed page number")
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    section_title: Optional[str] = None
    chemical_entities: List[str] = Field(default_factory=list)
    chunk_type: str = Field(default="text")
    payload: Dict[str, Any] = Field(default_factory=dict)

class RetrievalResponse(BaseModel):
    query_text: str
    workspace_id: str
    results: List[RetrievedChunk] = Field(default_factory=list)
    total_retrieved: int = 0
