import json
import pytest
from httpx import AsyncClient
from app.models.workspace import Workspace


@pytest.mark.asyncio
async def test_chat_query_sync_success(
    async_client: AsyncClient,
    sample_workspace: Workspace,
    auth_headers: dict,
):
    # 1. Create a conversation
    conv_res = await async_client.post(
        f"/api/v1/workspaces/{sample_workspace.id}/conversations",
        json={"title": "RAG Chat Test"},
        headers=auth_headers,
    )
    conv_id = conv_res.json()["id"]

    # 2. Post synchronous chat query
    chat_payload = {
        "prompt": "What is the catalyst concentration and reaction solvent?",
        "model_provider": "ollama",
        "selected_document_ids": ["doc_001"],
    }
    response = await async_client.post(
        f"/api/v1/workspaces/{sample_workspace.id}/conversations/{conv_id}/chat",
        json=chat_payload,
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["sender"] == "assistant"
    assert "content" in data
    assert len(data["content"]) > 0
    assert "citations" in data
    assert isinstance(data["citations"], list)


@pytest.mark.asyncio
async def test_chat_query_sse_streaming_success(
    async_client: AsyncClient,
    sample_workspace: Workspace,
    auth_headers: dict,
):
    conv_res = await async_client.post(
        f"/api/v1/workspaces/{sample_workspace.id}/conversations",
        json={"title": "Streaming Test"},
        headers=auth_headers,
    )
    conv_id = conv_res.json()["id"]

    chat_payload = {
        "prompt": "Explain the step-by-step mechanism of Suzuki coupling",
        "model_provider": "ollama",
    }
    response = await async_client.post(
        f"/api/v1/workspaces/{sample_workspace.id}/conversations/{conv_id}/chat/stream",
        json=chat_payload,
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")

    # Read SSE events
    body_text = response.text
    assert "data:" in body_text
    assert "token" in body_text


@pytest.mark.asyncio
async def test_chat_query_unauthorized_user_fails(
    async_client: AsyncClient,
    sample_workspace: Workspace,
    auth_headers: dict,
    secondary_auth_headers: dict,
):
    conv_res = await async_client.post(
        f"/api/v1/workspaces/{sample_workspace.id}/conversations",
        json={"title": "Private Conv"},
        headers=auth_headers,
    )
    conv_id = conv_res.json()["id"]

    response = await async_client.post(
        f"/api/v1/workspaces/{sample_workspace.id}/conversations/{conv_id}/chat",
        json={"prompt": "Unauthorized query"},
        headers=secondary_auth_headers,
    )
    assert response.status_code == 403
