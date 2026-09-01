import io
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile
from app.models.user import User
from app.models.workspace import Workspace
from app.models.document import Document
from app.models.conversation import Conversation, Message
from app.services.storage import storage_service
from app.services.usage import usage_service
from app.services.ai_gateway import ai_gateway


@pytest.mark.asyncio
async def test_storage_and_usage_integration(
    db_session: AsyncSession,
    sample_workspace: Workspace,
    test_user: User,
    temp_storage_dir: str,
):
    pdf_bytes = b"%PDF-1.4 Artificial photosynthesis catalyst report..."
    upload_file = UploadFile(
        file=io.BytesIO(pdf_bytes),
        filename="photosynthesis.pdf",
    )

    # 1. StorageService saves file and calculates checksum
    target_path, checksum, file_size = await storage_service.save_upload_file(
        sample_workspace.id, upload_file
    )
    assert len(checksum) == 64  # SHA256 hex length
    assert file_size == len(pdf_bytes)

    # 2. Record Document in DB
    doc = Document(
        workspace_id=sample_workspace.id,
        uploaded_by_id=test_user.id,
        filename="photosynthesis.pdf",
        file_size=file_size,
        mime_type="application/pdf",
        storage_path=target_path,
        status="PROCESSED",
    )
    db_session.add(doc)

    # 3. UsageService records document upload and storage bytes
    await usage_service.record_usage(db_session, sample_workspace.id, test_user.id, "documents_uploaded", 1)
    await usage_service.record_usage(db_session, sample_workspace.id, test_user.id, "storage_bytes", file_size)

    # 4. Verify usage summary reflects new counts
    summary = await usage_service.get_workspace_usage_summary(db_session, sample_workspace.id)
    assert summary.documents_count == 1
    assert summary.storage_bytes == file_size

    # Clean up file
    storage_service.delete_file(target_path)


@pytest.mark.asyncio
async def test_ai_gateway_and_chat_integration(
    db_session: AsyncSession,
    sample_workspace: Workspace,
    test_user: User,
):
    conv = Conversation(
        workspace_id=sample_workspace.id,
        user_id=test_user.id,
        title="Integration Chat Test",
    )
    db_session.add(conv)
    await db_session.commit()

    # 1. Check quota availability
    await usage_service.check_quota_available(db_session, sample_workspace.id, "ai_requests", 1)

    # 2. Execute AIGateway response generation
    prompt = "Explain organometallic catalyst regeneration steps."
    answer, citations = await ai_gateway.generate_rag_response(
        prompt=prompt,
        workspace_id=sample_workspace.id,
        model_provider="mock",
    )
    assert len(answer) > 0
    assert isinstance(citations, list)

    # 3. Record Assistant message & usage in DB
    msg = Message(
        conversation_id=conv.id,
        sender="assistant",
        content=answer,
    )
    db_session.add(msg)
    await usage_service.record_usage(db_session, sample_workspace.id, test_user.id, "ai_requests", 1)
    await db_session.commit()

    # 4. Verify AI request was counted
    summary = await usage_service.get_workspace_usage_summary(db_session, sample_workspace.id)
    assert summary.ai_requests_count == 1
