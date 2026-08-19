from datetime import datetime
from pydantic import BaseModel, ConfigDict


class UsageRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    user_id: str
    metric_type: str
    count: int
    created_at: datetime
    updated_at: datetime


class QuotaLimits(BaseModel):
    max_documents: int
    max_storage_mb: int
    max_ai_requests: int


class WorkspaceUsageSummary(BaseModel):
    workspace_id: str
    documents_count: int
    storage_bytes: int
    storage_mb: float
    ai_requests_count: int
    limits: QuotaLimits
