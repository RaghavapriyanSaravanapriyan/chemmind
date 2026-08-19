import json
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.v1.endpoints.conversations import get_conversation_with_permission
from app.models.conversation import Citation, Message
from app.models.user import User
from app.schemas.ai import AIChatRequest, AIChatResponse
from app.schemas.conversation import CitationRead
from app.services.ai_gateway import ai_gateway

router = APIRouter()


@router.post(
    "/{workspace_id}/conversations/{conversation_id}/chat",
    response_model=AIChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Synchronous AI RAG Chat Query",
)
async def chat_query(
    workspace_id: str,
    conversation_id: str,
    request: AIChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    conversation, role = await get_conversation_with_permission(
        workspace_id, conversation_id, current_user.id, db
    )

    if role not in ["owner", "editor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owners or editors can send chat messages",
        )

    # 1. Save user query message
    user_msg = Message(
        conversation_id=conversation.id,
        sender="user",
        content=request.prompt,
    )
    db.add(user_msg)
    await db.flush()

    # 2. Call AI Gateway
    answer_text, citations_in = await ai_gateway.generate_rag_response(
        prompt=request.prompt,
        workspace_id=workspace_id,
        selected_document_ids=request.selected_document_ids,
        model_provider=request.model_provider,
    )

    # 3. Save assistant message
    asst_msg = Message(
        conversation_id=conversation.id,
        sender="assistant",
        content=answer_text,
    )
    db.add(asst_msg)
    await db.flush()

    # 4. Save citation metadata
    citation_objs: list[Citation] = []
    for cit in citations_in:
        citation = Citation(
            message_id=asst_msg.id,
            document_id=cit.document_id,
            page=cit.page,
            chunk_id=cit.chunk_id,
            section=cit.section,
            excerpt=cit.excerpt,
        )
        db.add(citation)
        citation_objs.append(citation)

    await db.commit()
    await db.refresh(asst_msg)

    citation_reads = [CitationRead.model_validate(c) for c in asst_msg.citations]
    return AIChatResponse(
        message_id=asst_msg.id,
        sender="assistant",
        content=asst_msg.content,
        citations=citation_reads,
    )


@router.post(
    "/{workspace_id}/conversations/{conversation_id}/chat/stream",
    summary="Realtime SSE Token Streaming Chat Query",
)
async def chat_stream(
    workspace_id: str,
    conversation_id: str,
    request: AIChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EventSourceResponse:
    conversation, role = await get_conversation_with_permission(
        workspace_id, conversation_id, current_user.id, db
    )

    if role not in ["owner", "editor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owners or editors can stream chat messages",
        )

    # Save user message first
    user_msg = Message(
        conversation_id=conversation.id,
        sender="user",
        content=request.prompt,
    )
    db.add(user_msg)
    await db.commit()

    async def event_generator():
        full_content = ""
        final_citations = []

        async for chunk in ai_gateway.stream_rag_response(
            prompt=request.prompt,
            workspace_id=workspace_id,
            selected_document_ids=request.selected_document_ids,
            model_provider=request.model_provider,
        ):
            if chunk.get("token"):
                full_content += chunk["token"]
            if chunk.get("finish_reason") == "stop":
                full_content = chunk.get("full_content", full_content)
                final_citations = chunk.get("citations", [])

            yield {"data": json.dumps(chunk)}

        # Persist complete assistant message and citations in DB
        asst_msg = Message(
            conversation_id=conversation.id,
            sender="assistant",
            content=full_content,
        )
        db.add(asst_msg)
        await db.flush()

        for cit_dict in final_citations:
            citation = Citation(
                message_id=asst_msg.id,
                document_id=cit_dict.get("document_id"),
                page=cit_dict.get("page"),
                chunk_id=cit_dict.get("chunk_id"),
                section=cit_dict.get("section"),
                excerpt=cit_dict.get("excerpt"),
            )
            db.add(citation)

        await db.commit()

    return EventSourceResponse(event_generator())
