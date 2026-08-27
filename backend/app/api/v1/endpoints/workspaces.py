from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceMemberAdd,
    WorkspaceMemberRead,
    WorkspaceRead,
    WorkspaceUpdate,
)

router = APIRouter()


async def get_workspace_with_user_role(
    workspace_id: str, user_id: str, db: AsyncSession
) -> tuple[Workspace, str]:
    # Query workspace
    result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    workspace = result.scalar_one_or_none()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )



    # Check if user is owner directly
    if workspace.owner_id == user_id:
        return workspace, "owner"

    # Check if user is member
    member_result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    )
    member = member_result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this workspace",
        )

    return workspace, member.role


@router.post("", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED, summary="Create Workspace")
async def create_workspace(
    workspace_in: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    # Create workspace
    workspace = Workspace(
        name=workspace_in.name,
        description=workspace_in.description,
        owner_id=current_user.id,
        is_archived=False,
    )
    db.add(workspace)
    await db.flush()

    # Create owner membership record
    owner_member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=current_user.id,
        role="owner",
    )
    db.add(owner_member)
    await db.commit()
    await db.refresh(workspace)
    return workspace


@router.get("", response_model=List[WorkspaceRead], summary="List Workspaces")
async def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    # Find workspaces where user is owner or member
    stmt = (
        select(Workspace)
        .outerjoin(WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id)
        .where(
            or_(
                Workspace.owner_id == current_user.id,
                WorkspaceMember.user_id == current_user.id,
            )
        )
        .distinct()
    )
    result = await db.execute(stmt)
    workspaces = result.scalars().all()
    return workspaces


@router.get("/{workspace_id}", response_model=WorkspaceRead, summary="Get Workspace by ID")
async def get_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    workspace, _ = await get_workspace_with_user_role(workspace_id, current_user.id, db)
    return workspace


@router.put("/{workspace_id}", response_model=WorkspaceRead, summary="Update Workspace")
async def update_workspace(
    workspace_id: str,
    workspace_in: WorkspaceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    workspace, role = await get_workspace_with_user_role(workspace_id, current_user.id, db)

    if role not in ["owner", "editor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owners or editors can update workspace details",
        )

    if workspace_in.name is not None:
        workspace.name = workspace_in.name
    if workspace_in.description is not None:
        workspace.description = workspace_in.description
    if workspace_in.is_archived is not None:
        workspace.is_archived = workspace_in.is_archived

    await db.commit()
    await db.refresh(workspace)
    return workspace


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Workspace")
async def delete_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    workspace, role = await get_workspace_with_user_role(workspace_id, current_user.id, db)

    if role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the workspace owner can delete a workspace",
        )

    await db.delete(workspace)
    await db.commit()
    return None


@router.post("/{workspace_id}/members", response_model=WorkspaceMemberRead, status_code=status.HTTP_201_CREATED, summary="Add Workspace Member")
async def add_workspace_member(
    workspace_id: str,
    member_in: WorkspaceMemberAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    workspace, role = await get_workspace_with_user_role(workspace_id, current_user.id, db)

    if role not in ["owner", "editor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owners or editors can add members",
        )

    # Check if target user exists
    user_res = await db.execute(select(User).where(User.id == member_in.user_id))
    target_user = user_res.scalar_one_or_none()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user to add not found",
        )

    # Check if already member
    existing_member_res = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == member_in.user_id,
        )
    )
    if existing_member_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this workspace",
        )

    new_member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=member_in.user_id,
        role=member_in.role,
    )
    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)
    return new_member
