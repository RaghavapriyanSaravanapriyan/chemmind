import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.models.document import Document, DocumentMetadata
from app.models.conversation import Conversation, Message, Citation


@pytest.mark.asyncio
async def test_database_health_ping(db_session: AsyncSession):
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


@pytest.mark.asyncio
async def test_cascade_delete_workspace_cleans_child_records(
    db_session: AsyncSession,
    test_user: User,
):
    # 1. Create Workspace
    ws = Workspace(
        id="ws_cascade_001",
        name="Cascade Test Workspace",
        description="Testing cascading deletions",
        owner_id=test_user.id,
    )
    db_session.add(ws)
    await db_session.flush()

    # 2. Add Member
    member = WorkspaceMember(workspace_id=ws.id, user_id=test_user.id, role="owner")
    db_session.add(member)

    # 3. Add Document and Metadata
    doc = Document(
        id="doc_cascade_001",
        workspace_id=ws.id,
        uploaded_by_id=test_user.id,
        filename="cascade_doc.pdf",
        storage_path="/tmp/fake.pdf",
    )
    db_session.add(doc)
    await db_session.flush()

    meta = DocumentMetadata(document_id=doc.id, checksum="fake_sha256", title="Cascade Doc")
    db_session.add(meta)

    # 4. Add Conversation, Message, and Citation
    conv = Conversation(id="conv_cascade_001", workspace_id=ws.id, user_id=test_user.id, title="Cascade Conv")
    db_session.add(conv)
    await db_session.flush()

    msg = Message(id="msg_cascade_001", conversation_id=conv.id, sender="assistant", content="Grounded answer [1]")
    db_session.add(msg)
    await db_session.flush()

    cit = Citation(message_id=msg.id, document_id=doc.id, page=1, excerpt="Evidence excerpt")
    db_session.add(cit)
    await db_session.commit()

    # Verify all records exist
    res_ws = await db_session.execute(select(Workspace).where(Workspace.id == ws.id))
    assert res_ws.scalar_one_or_none() is not None

    # Delete Workspace
    await db_session.delete(ws)
    await db_session.commit()

    # Verify workspace is gone
    res_ws_after = await db_session.execute(select(Workspace).where(Workspace.id == ws.id))
    assert res_ws_after.scalar_one_or_none() is None

    # Verify cascade deleted members
    res_mem = await db_session.execute(select(WorkspaceMember).where(WorkspaceMember.workspace_id == ws.id))
    assert res_mem.scalars().all() == []

    # Verify cascade deleted conversations
    res_conv = await db_session.execute(select(Conversation).where(Conversation.workspace_id == ws.id))
    assert res_conv.scalars().all() == []


@pytest.mark.asyncio
async def test_transaction_rollback_preserves_consistency(
    db_session: AsyncSession,
    test_user: User,
):
    initial_users_count = len((await db_session.execute(select(User))).scalars().all())

    # Start a transaction and rollback
    try:
        new_user = User(
            id="user_rollback_001",
            email="rollback_user@chemmind.org",
            full_name="Rollback User",
            hashed_password="some_hashed_password",
        )
        db_session.add(new_user)
        await db_session.flush()
        # Simulate deliberate error
        raise RuntimeError("Simulated transaction failure")
    except RuntimeError:
        await db_session.rollback()

    # Verify the aborted user was not saved
    users_after = (await db_session.execute(select(User))).scalars().all()
    assert len(users_after) == initial_users_count
    assert not any(u.id == "user_rollback_001" for u in users_after)
