from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from ai.schemas.document import DocumentMetadata

class BlockType(str, Enum):
    TEXT = "text"
    HEADING = "heading"
    TABLE = "table"
    EQUATION = "equation"
    FIGURE = "figure"

class ExtractedBlock(BaseModel):
    block_id: str
    page_number: int = Field(..., description="1-indexed page number")
    block_type: BlockType = BlockType.TEXT
    text: str
    section_title: Optional[str] = None
    bbox: Optional[List[float]] = Field(
        default=None,
        description="Bounding box [x0, y0, x1, y1] if available"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ParsedPage(BaseModel):
    page_number: int = Field(..., description="1-indexed page number")
    text: str
    blocks: List[ExtractedBlock] = Field(default_factory=list)
    image_count: int = 0
    table_count: int = 0

class IngestedDocument(BaseModel):
    document_id: str
    workspace_id: str
    filename: str
    metadata: DocumentMetadata
    pages: List[ParsedPage] = Field(default_factory=list)
    total_pages: int = 0
    total_blocks: int = 0
