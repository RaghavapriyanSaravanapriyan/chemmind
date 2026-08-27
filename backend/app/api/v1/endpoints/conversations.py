from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.v1.endpoints.workspaces import get_workspace_with_user_role
from app.models.conversation import Citation, Conversation, Message
from app.models.user import User
from app.schemas.conversation import (
    ConversationCreate,
    ConversationRead,
    ConversationUpdate,
    MessageCreate,
    MessageRead,
)

router = APIRouter()


async def get_conversation_with_permission(
    workspace_id: str,
    conversation_id: str,
    user_id: str,
    db: AsyncSession,
) -> tuple[Conversation, str]:
    workspace, role = await get_workspace_with_user_role(workspace_id, user_id, db)

    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.workspace_id == workspace_id,
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )



    return conversation, role


@router.post(
    "/{workspace_id}/conversations",
    response_model=ConversationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Conversation",
)
async def create_conversation(
    workspace_id: str,
    conv_in: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    await get_workspace_with_user_role(workspace_id, current_user.id, db)

    conversation = Conversation(
        workspace_id=workspace_id,
        user_id=current_user.id,
        title=conv_in.title,
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


@router.get(
    "/{workspace_id}/conversations",
    response_model=List[ConversationRead],
    summary="List Conversations",
)
async def list_conversations(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    await get_workspace_with_user_role(workspace_id, current_user.id, db)

    result = await db.execute(
        select(Conversation)
        .where(Conversation.workspace_id == workspace_id)
        .order_by(Conversation.updated_at.desc())
    )
    conversations = result.scalars().all()
    return conversations


@router.get(
    "/{workspace_id}/conversations/{conversation_id}",
    response_model=ConversationRead,
    summary="Get Conversation Details and Message History",
)
async def get_conversation(
    workspace_id: str,
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    conversation, _ = await get_conversation_with_permission(
        workspace_id, conversation_id, current_user.id, db
    )
    return conversation


@router.post(
    "/{workspace_id}/conversations/{conversation_id}/messages",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add Message to Conversation",
)
async def add_message(
    workspace_id: str,
    conversation_id: str,
    message_in: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    conversation, role = await get_conversation_with_permission(
        workspace_id, conversation_id, current_user.id, db
    )

    if role not in ["owner", "editor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owners or editors can add messages",
        )

    # Create Message
    message = Message(
        conversation_id=conversation.id,
        sender=message_in.sender,
        content=message_in.content,
    )
    db.add(message)
    await db.flush()

    # Add Citations if provided
    for cit_in in message_in.citations:
        citation = Citation(
            message_id=message.id,
            document_id=cit_in.document_id,
            page=cit_in.page,
            chunk_id=cit_in.chunk_id,
            section=cit_in.section,
            excerpt=cit_in.excerpt,
        )
        db.add(citation)

    await db.commit()
    await db.refresh(message)
    return message


@router.delete(
    "/{workspace_id}/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Conversation",
)
async def delete_conversation(
    workspace_id: str,
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    conversation, role = await get_conversation_with_permission(
        workspace_id, conversation_id, current_user.id, db
    )

    if role not in ["owner", "editor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owners or editors can delete conversations",
        )

    await db.delete(conversation)
    await db.commit()
    return None
