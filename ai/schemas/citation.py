from typing import List, Optional
from pydantic import BaseModel, Field

class SourceLocation(BaseModel):
    page_number: int = Field(..., description="1-indexed page number in the source document")
    section_title: Optional[str] = Field(default=None, description="Title of section/heading if available")
    bbox: Optional[List[float]] = Field(
        default=None,
        description="Bounding box coordinates [x0, y0, x1, y1] on page normalized [0,1] or points"
    )

class Citation(BaseModel):
    citation_id: Optional[str] = None
    workspace_id: str
    document_id: str
    chunk_id: str
    document_title: str
    excerpt: str = Field(..., description="The grounded excerpt from the source text")
    location: SourceLocation
