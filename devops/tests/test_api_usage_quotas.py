import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.workspace import Workspace
from app.services.usage import usage_service


@pytest.mark.asyncio
async def test_get_workspace_usage_summary(
    async_client: AsyncClient,
    sample_workspace: Workspace,
    auth_headers: dict,
):
    response = await async_client.get(
        f"/api/v1/workspaces/{sample_workspace.id}/usage",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["workspace_id"] == sample_workspace.id
    assert "documents_count" in data
    assert "storage_bytes" in data
    assert "storage_mb" in data
    assert "ai_requests_count" in data
    assert "limits" in data
    assert data["limits"]["max_documents"] > 0
    assert data["limits"]["max_storage_mb"] > 0
    assert data["limits"]["max_ai_requests"] > 0


@pytest.mark.asyncio
async def test_usage_service_document_quota_exceeded(
    db_session: AsyncSession,
    sample_workspace: Workspace,
    test_user,
):
    # Set document count to max limit
    summary = await usage_service.get_workspace_usage_summary(db_session, sample_workspace.id)
    max_docs = summary.limits.max_documents

    await usage_service.record_usage(
        db_session, sample_workspace.id, test_user.id, "documents_uploaded", max_docs
    )

    # Attempting to upload 1 more document should raise 429
    with pytest.raises(HTTPException) as exc_info:
        await usage_service.check_quota_available(
            db_session, sample_workspace.id, "documents_uploaded", 1
        )
    assert exc_info.value.status_code == 429
    assert "quota limit" in exc_info.value.detail


@pytest.mark.asyncio
async def test_usage_service_storage_quota_exceeded(
    db_session: AsyncSession,
    sample_workspace: Workspace,
    test_user,
):
    summary = await usage_service.get_workspace_usage_summary(db_session, sample_workspace.id)
    max_storage_bytes = summary.limits.max_storage_mb * 1024 * 1024

    await usage_service.record_usage(
        db_session, sample_workspace.id, test_user.id, "storage_bytes", max_storage_bytes
    )

    # Attempting to add 1 MB more should raise 413
    with pytest.raises(HTTPException) as exc_info:
        await usage_service.check_quota_available(
            db_session, sample_workspace.id, "storage_bytes", 1024 * 1024
        )
    assert exc_info.value.status_code == 413


@pytest.mark.asyncio
async def test_usage_service_ai_request_quota_exceeded(
    db_session: AsyncSession,
    sample_workspace: Workspace,
    test_user,
):
    summary = await usage_service.get_workspace_usage_summary(db_session, sample_workspace.id)
    max_ai = summary.limits.max_ai_requests

    await usage_service.record_usage(
        db_session, sample_workspace.id, test_user.id, "ai_requests", max_ai
    )

    with pytest.raises(HTTPException) as exc_info:
        await usage_service.check_quota_available(
            db_session, sample_workspace.id, "ai_requests", 1
        )
    assert exc_info.value.status_code == 429
