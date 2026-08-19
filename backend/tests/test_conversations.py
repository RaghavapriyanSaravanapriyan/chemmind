import io
import pytest
from httpx import AsyncClient
from tests.test_workspaces import create_user_and_login


@pytest.mark.asyncio
async def test_create_conversation_success(async_client: AsyncClient):
    user, token = await create_user_and_login(async_client, "conv_user1@chemmind.org", "Conv User 1")
    headers = {"Authorization": f"Bearer {token}"}

    # Create workspace
    ws_res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "Quantum Chat Lab"},
        headers=headers,
    )
    ws_id = ws_res.json()["id"]

    # Create conversation
    payload = {"title": "Discussion on Density Functional Theory"}
    response = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/conversations",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["workspace_id"] == ws_id
    assert data["user_id"] == user["id"]
    assert "messages" in data


@pytest.mark.asyncio
async def test_add_messages_with_citations(async_client: AsyncClient):
    _, token = await create_user_and_login(async_client, "conv_user2@chemmind.org", "Conv User 2")
    headers = {"Authorization": f"Bearer {token}"}

    ws_res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "RAG Research Space"},
        headers=headers,
    )
    ws_id = ws_res.json()["id"]

    # Upload document
    pdf_bytes = b"%PDF-1.4 paper content..."
    files = {"file": ("dft_paper.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    doc_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/documents",
        files=files,
        headers=headers,
    )
    doc_id = doc_res.json()["id"]

    # Create conversation
    conv_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/conversations",
        json={"title": "RAG Q&A Session"},
        headers=headers,
    )
    conv_id = conv_res.json()["id"]

    # Add user message
    user_msg_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/conversations/{conv_id}/messages",
        json={"sender": "user", "content": "What energy functional is used?"},
        headers=headers,
    )
    assert user_msg_res.status_code == 201

    # Add assistant response with citations
    assistant_msg_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/conversations/{conv_id}/messages",
        json={
            "sender": "assistant",
            "content": "The paper utilizes the B3LYP hybrid functional [p.14].",
            "citations": [
                {
                    "document_id": doc_id,
                    "page": 14,
                    "chunk_id": "chunk-9921",
                    "section": "Methods",
                    "excerpt": "B3LYP hybrid functional was chosen for exchange-correlation calculations.",
                }
            ],
        },
        headers=headers,
    )
    assert assistant_msg_res.status_code == 201
    asst_data = assistant_msg_res.json()
    assert len(asst_data["citations"]) == 1
    assert asst_data["citations"][0]["page"] == 14
    assert asst_data["citations"][0]["chunk_id"] == "chunk-9921"

    # Fetch conversation details & check full message history
    history_res = await async_client.get(
        f"/api/v1/workspaces/{ws_id}/conversations/{conv_id}",
        headers=headers,
    )
    assert history_res.status_code == 200
    hist_data = history_res.json()
    assert len(hist_data["messages"]) == 2


@pytest.mark.asyncio
async def test_conversation_access_isolation(async_client: AsyncClient):
    # User 1 creates conversation
    _, token1 = await create_user_and_login(async_client, "owner_conv@chemmind.org", "Owner Conv")
    ws_res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "Owner Private Space"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    ws_id = ws_res.json()["id"]

    conv_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/conversations",
        json={"title": "Confidential Chat"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    conv_id = conv_res.json()["id"]

    # User 2 attempts to fetch conversation
    _, token2 = await create_user_and_login(async_client, "outsider_conv@chemmind.org", "Outsider Conv")
    get_res = await async_client.get(
        f"/api/v1/workspaces/{ws_id}/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert get_res.status_code == 403


@pytest.mark.asyncio
async def test_delete_conversation(async_client: AsyncClient):
    _, token = await create_user_and_login(async_client, "deleter_conv@chemmind.org", "Deleter Conv")
    headers = {"Authorization": f"Bearer {token}"}

    ws_res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "Temp Conv Space"},
        headers=headers,
    )
    ws_id = ws_res.json()["id"]

    conv_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/conversations",
        json={"title": "To Delete"},
        headers=headers,
    )
    conv_id = conv_res.json()["id"]

    # Delete
    del_res = await async_client.delete(
        f"/api/v1/workspaces/{ws_id}/conversations/{conv_id}",
        headers=headers,
    )
    assert del_res.status_code == 204

    # Verify 404
    get_res = await async_client.get(
        f"/api/v1/workspaces/{ws_id}/conversations/{conv_id}",
        headers=headers,
    )
    assert get_res.status_code == 404
