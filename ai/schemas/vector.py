from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class VectorPoint(BaseModel):
    id: str = Field(..., description="Unique vector point ID or chunk UUID")
    vector: List[float] = Field(..., description="Dense embedding vector")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Metadata payload (workspace, doc_id, text, page, section)")

class VectorSearchResult(BaseModel):
    chunk_id: str
    score: float = Field(..., description="Similarity score (e.g. cosine distance/similarity)")
    text: str
    workspace_id: str
    document_id: str
    page_number: int
    section_title: Optional[str] = None
    chemical_entities: List[str] = Field(default_factory=list)
    chunk_type: str = "text"
    payload: Dict[str, Any] = Field(default_factory=dict)
