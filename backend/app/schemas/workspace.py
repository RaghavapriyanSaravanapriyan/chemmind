from datetime import datetime
from pydantic import BaseModel, ConfigDict


class WorkspaceBase(BaseModel):
    name: str
    description: str | None = None


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_archived: bool | None = None


class WorkspaceRead(WorkspaceBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class WorkspaceMemberAdd(BaseModel):
    user_id: str
    role: str = "editor"  # owner, editor, viewer


class WorkspaceMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    user_id: str
    role: str
    created_at: datetime
