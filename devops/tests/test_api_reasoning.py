import pytest
from httpx import AsyncClient
from app.models.workspace import Workspace


@pytest.mark.asyncio
async def test_multi_doc_reasoning_success(
    async_client: AsyncClient,
    sample_workspace: Workspace,
    auth_headers: dict,
):
    payload = {
        "query_text": "Compare catalytic yields and reaction temperatures reported across studies.",
        "document_ids": ["doc_paper_001", "doc_paper_002"],
    }
    response = await async_client.post(
        f"/api/v1/workspaces/{sample_workspace.id}/reasoning/multi-doc",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "comparison_matrix" in data
    assert "discrepancies" in data
    assert data["workspace_id"] == sample_workspace.id


@pytest.mark.asyncio
async def test_multi_doc_reasoning_empty_documents_fails(
    async_client: AsyncClient,
    sample_workspace: Workspace,
    auth_headers: dict,
):
    payload = {
        "query_text": "Compare papers",
        "document_ids": [],  # Min items is 1
    }
    response = await async_client.post(
        f"/api/v1/workspaces/{sample_workspace.id}/reasoning/multi-doc",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 422
