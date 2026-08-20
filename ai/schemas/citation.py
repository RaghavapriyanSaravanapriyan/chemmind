from typing import List, Optional
from pydantic import BaseModel, Field

class SourceLocation(BaseModel):
    page_number: Optional[int] = Field(default=None, description="1-indexed page number in the source document")
    section_title: Optional[str] = Field(default=None, description="Title of section/heading if available")
    bbox: Optional[List[float]] = Field(
        default=None,
        description="Bounding box coordinates [x0, y0, x1, y1] on page normalized [0,1] or points"
    )

class Citation(BaseModel):
    citation_id: Optional[str] = None
    workspace_id: str
    document_id: Optional[str] = None
    chunk_id: Optional[str] = None
    document_title: Optional[str] = None
    excerpt: str = Field(..., description="The grounded excerpt from the source text or web snippet")
    location: Optional[SourceLocation] = None
    source_type: str = Field(default="document", description="Type of source: 'document' or 'web'")
    url: Optional[str] = Field(default=None, description="Clickable URL for web citations")
    title: Optional[str] = Field(default=None, description="Title of document or web source")
    domain: Optional[str] = Field(default=None, description="Domain name for web source")

