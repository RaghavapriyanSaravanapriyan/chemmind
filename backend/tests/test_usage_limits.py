import io
import pytest
from httpx import AsyncClient
from app.core.config import settings
from tests.test_workspaces import create_user_and_login


@pytest.mark.asyncio
async def test_get_workspace_usage_summary(async_client: AsyncClient):
    user, token = await create_user_and_login(async_client, "usage_user1@chemmind.org", "Usage User 1")
    headers = {"Authorization": f"Bearer {token}"}

    # Create workspace
    ws_res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "Usage Tracking Space"},
        headers=headers,
    )
    ws_id = ws_res.json()["id"]

    # Initial summary check
    usage_res = await async_client.get(f"/api/v1/workspaces/{ws_id}/usage", headers=headers)
    assert usage_res.status_code == 200
    data = usage_res.json()
    assert data["workspace_id"] == ws_id
    assert data["documents_count"] == 0
    assert data["ai_requests_count"] == 0
    assert data["limits"]["max_documents"] == settings.DEFAULT_WORKSPACE_DOC_LIMIT


@pytest.mark.asyncio
async def test_usage_increment_on_upload_and_chat(async_client: AsyncClient):
    _, token = await create_user_and_login(async_client, "usage_user2@chemmind.org", "Usage User 2")
    headers = {"Authorization": f"Bearer {token}"}

    ws_res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "Active Metric Space"},
        headers=headers,
    )
    ws_id = ws_res.json()["id"]

    # Upload PDF
    pdf_bytes = b"%PDF-1.4 sample content for metric tracking..."
    files = {"file": ("metric_paper.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    await async_client.post(f"/api/v1/workspaces/{ws_id}/documents", files=files, headers=headers)

    # Create conversation & query chat
    conv_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/conversations",
        json={"title": "Usage Chat"},
        headers=headers,
    )
    conv_id = conv_res.json()["id"]

    await async_client.post(
        f"/api/v1/workspaces/{ws_id}/conversations/{conv_id}/chat",
        json={"prompt": "Calculate properties"},
        headers=headers,
    )

    # Check updated metrics
    usage_res = await async_client.get(f"/api/v1/workspaces/{ws_id}/usage", headers=headers)
    assert usage_res.status_code == 200
    data = usage_res.json()
    assert data["documents_count"] == 1
    assert data["ai_requests_count"] == 1
    assert data["storage_bytes"] == len(pdf_bytes)


@pytest.mark.asyncio
async def test_quota_exceeded_enforcement(async_client: AsyncClient):
    _, token = await create_user_and_login(async_client, "usage_user3@chemmind.org", "Usage User 3")
    headers = {"Authorization": f"Bearer {token}"}

    ws_res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "Strict Quota Space"},
        headers=headers,
    )
    ws_id = ws_res.json()["id"]

    # Artificially set tight doc limit for testing
    original_limit = settings.DEFAULT_WORKSPACE_DOC_LIMIT
    settings.DEFAULT_WORKSPACE_DOC_LIMIT = 1

    try:
        # First upload - should succeed
        files1 = {"file": ("paper1.pdf", io.BytesIO(b"%PDF-1.4 sample 1"), "application/pdf")}
        res1 = await async_client.post(f"/api/v1/workspaces/{ws_id}/documents", files=files1, headers=headers)
        assert res1.status_code == 201

        # Second upload - should fail with 429 quota exceeded
        files2 = {"file": ("paper2.pdf", io.BytesIO(b"%PDF-1.4 sample 2"), "application/pdf")}
        res2 = await async_client.post(f"/api/v1/workspaces/{ws_id}/documents", files=files2, headers=headers)
        assert res2.status_code == 429
        assert "quota limit" in res2.json()["detail"]

    finally:
        settings.DEFAULT_WORKSPACE_DOC_LIMIT = original_limit
