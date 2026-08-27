from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.v1.endpoints.workspaces import get_workspace_with_user_role
from app.models.user import User
from app.schemas.usage import WorkspaceUsageSummary
from app.services.usage import usage_service

router = APIRouter()


@router.get(
    "/{workspace_id}/usage",
    response_model=WorkspaceUsageSummary,
    summary="Get Workspace Usage Summary and Quotas",
)
async def get_workspace_usage(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    await get_workspace_with_user_role(workspace_id, current_user.id, db)
    summary = await usage_service.get_workspace_usage_summary(db, workspace_id)
    return summary
