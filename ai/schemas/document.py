from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class DocumentMetadata(BaseModel):
    title: str
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    mime_type: str = "application/pdf"
    file_size_bytes: Optional[int] = None
    total_pages: Optional[int] = None
    checksum: Optional[str] = None
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)

class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    workspace_id: str
    text: str
    page_number: int = Field(..., description="1-indexed page number")
    section_title: Optional[str] = None
    chemical_entities: List[str] = Field(default_factory=list)
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
