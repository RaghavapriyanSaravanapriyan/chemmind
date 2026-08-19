from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DocumentMetadataRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    page_count: int | None = None
    title: str | None = None
    author: str | None = None
    checksum: str | None = None


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    uploaded_by_id: str
    filename: str
    file_size: int
    mime_type: str
    storage_path: str
    status: str
    created_at: datetime
    updated_at: datetime
    doc_metadata: DocumentMetadataRead | None = None


class DocumentStatusUpdate(BaseModel):
    status: str
