import io
import json
import pytest
from httpx import AsyncClient
from tests.test_workspaces import create_user_and_login


@pytest.mark.asyncio
async def test_synchronous_chat_query(async_client: AsyncClient):
    user, token = await create_user_and_login(async_client, "ai_user1@chemmind.org", "AI User 1")
    headers = {"Authorization": f"Bearer {token}"}

    # Create workspace
    ws_res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "Molecular AI Workspace"},
        headers=headers,
    )
    ws_id = ws_res.json()["id"]

    # Upload document
    pdf_bytes = b"%PDF-1.4 molecular paper..."
    files = {"file": ("molecule_paper.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    doc_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/documents",
        files=files,
        headers=headers,
    )
    doc_id = doc_res.json()["id"]

    # Create conversation
    conv_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/conversations",
        json={"title": "AI Grounding Test"},
        headers=headers,
    )
    conv_id = conv_res.json()["id"]

    # Send synchronous chat request
    chat_payload = {
        "prompt": "What is the binding affinity of compound X?",
        "selected_document_ids": [doc_id],
        "model_provider": "ollama",
    }
    response = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/conversations/{conv_id}/chat",
        json=chat_payload,
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["sender"] == "assistant"
    assert "content" in data
    assert len(data["citations"]) >= 1
    assert data["citations"][0]["document_id"] == doc_id

    # Verify message history persisted in DB
    history_res = await async_client.get(
        f"/api/v1/workspaces/{ws_id}/conversations/{conv_id}",
        headers=headers,
    )
    assert history_res.status_code == 200
    hist_data = history_res.json()
    assert len(hist_data["messages"]) == 2  # user prompt + assistant answer


@pytest.mark.asyncio
async def test_sse_token_streaming_chat(async_client: AsyncClient):
    _, token = await create_user_and_login(async_client, "ai_user2@chemmind.org", "AI User 2")
    headers = {"Authorization": f"Bearer {token}"}

    ws_res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "SSE Streaming Workspace"},
        headers=headers,
    )
    ws_id = ws_res.json()["id"]

    conv_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/conversations",
        json={"title": "Streaming Test"},
        headers=headers,
    )
    conv_id = conv_res.json()["id"]

    chat_payload = {
        "prompt": "Explain the kinetic mechanism.",
        "model_provider": "ollama",
    }
    response = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/conversations/{conv_id}/chat/stream",
        json=chat_payload,
        headers=headers,
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")

    content_str = response.text
    assert "data:" in content_str

    # Verify messages auto-persisted after stream
    history_res = await async_client.get(
        f"/api/v1/workspaces/{ws_id}/conversations/{conv_id}",
        headers=headers,
    )
    assert history_res.status_code == 200
    assert len(history_res.json()["messages"]) == 2


@pytest.mark.asyncio
async def test_chat_access_isolation(async_client: AsyncClient):
    # User 1 creates workspace and conversation
    _, token1 = await create_user_and_login(async_client, "ai_owner@chemmind.org", "AI Owner")
    ws_res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "Private AI Space"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    ws_id = ws_res.json()["id"]

    conv_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/conversations",
        json={"title": "Private Chat"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    conv_id = conv_res.json()["id"]

    # User 2 attempts chat query
    _, token2 = await create_user_and_login(async_client, "ai_intruder@chemmind.org", "AI Intruder")
    chat_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/conversations/{conv_id}/chat",
        json={"prompt": "Unauthorized prompt"},
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert chat_res.status_code == 403
