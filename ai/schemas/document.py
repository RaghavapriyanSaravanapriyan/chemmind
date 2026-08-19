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
    page_number: int = Field(..., description="1-indexed primary page number")
    page_start: Optional[int] = Field(default=None, description="Starting page for multi-page chunks")
    page_end: Optional[int] = Field(default=None, description="Ending page for multi-page chunks")
    section_title: Optional[str] = None
    parent_section: Optional[str] = None
    chunk_type: str = Field(default="text", description="Type: text, equation, table_caption, figure_caption")
    chemical_entities: List[str] = Field(default_factory=list, description="Extracted chemical formulas, solvents, SMILES")
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    token_count_estimate: int = Field(default=0, description="Estimated token count (char_count // 4)")
    metadata: Dict[str, Any] = Field(default_factory=dict)
