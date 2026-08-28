import pytest
from httpx import AsyncClient
from app.models.workspace import Workspace


@pytest.mark.asyncio
async def test_create_conversation_success(
    async_client: AsyncClient,
    sample_workspace: Workspace,
    auth_headers: dict,
):
    payload = {"title": "Enantioselective Synthesis Discussion"}
    response = await async_client.post(
        f"/api/v1/workspaces/{sample_workspace.id}/conversations",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["workspace_id"] == sample_workspace.id
    assert "id" in data


@pytest.mark.asyncio
async def test_list_conversations(
    async_client: AsyncClient,
    sample_workspace: Workspace,
    auth_headers: dict,
):
    await async_client.post(
        f"/api/v1/workspaces/{sample_workspace.id}/conversations",
        json={"title": "Conv 1"},
        headers=auth_headers,
    )
    await async_client.post(
        f"/api/v1/workspaces/{sample_workspace.id}/conversations",
        json={"title": "Conv 2"},
        headers=auth_headers,
    )

    response = await async_client.get(
        f"/api/v1/workspaces/{sample_workspace.id}/conversations",
        headers=auth_headers,
    )
    assert response.status_code == 200
    convs = response.json()
    assert len(convs) >= 2


@pytest.mark.asyncio
async def test_add_message_with_citations(
    async_client: AsyncClient,
    sample_workspace: Workspace,
    auth_headers: dict,
):
    conv_res = await async_client.post(
        f"/api/v1/workspaces/{sample_workspace.id}/conversations",
        json={"title": "Reaction Discussion"},
        headers=auth_headers,
    )
    conv_id = conv_res.json()["id"]

    msg_payload = {
        "sender": "assistant",
        "content": "The reaction proceeds via oxidative addition [1].",
        "citations": [
            {
                "document_id": "doc_001",
                "page": 4,
                "section": "Mechanistic Investigation",
                "excerpt": "Oxidative addition was confirmed by spectroscopy.",
            }
        ],
    }

    msg_res = await async_client.post(
        f"/api/v1/workspaces/{sample_workspace.id}/conversations/{conv_id}/messages",
        json=msg_payload,
        headers=auth_headers,
    )
    assert msg_res.status_code == 201
    data = msg_res.json()
    assert data["content"] == msg_payload["content"]
    assert len(data["citations"]) == 1
    assert data["citations"][0]["page"] == 4


@pytest.mark.asyncio
async def test_delete_conversation_success(
    async_client: AsyncClient,
    sample_workspace: Workspace,
    auth_headers: dict,
):
    conv_res = await async_client.post(
        f"/api/v1/workspaces/{sample_workspace.id}/conversations",
        json={"title": "Temporary Conv"},
        headers=auth_headers,
    )
    conv_id = conv_res.json()["id"]

    del_res = await async_client.delete(
        f"/api/v1/workspaces/{sample_workspace.id}/conversations/{conv_id}",
        headers=auth_headers,
    )
    assert del_res.status_code == 204

    # Subsequent fetch returns 404
    get_res = await async_client.get(
        f"/api/v1/workspaces/{sample_workspace.id}/conversations/{conv_id}",
        headers=auth_headers,
    )
    assert get_res.status_code == 404
