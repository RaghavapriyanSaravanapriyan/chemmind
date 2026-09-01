import pytest
from httpx import AsyncClient
from app.models.user import User
from app.models.workspace import Workspace


@pytest.mark.asyncio
async def test_create_workspace_success(async_client: AsyncClient, test_user: User, auth_headers: dict):
    payload = {
        "name": "Supramolecular Assemblies",
        "description": "Research into non-covalent bonding and macrocycles",
    }
    response = await async_client.post("/api/v1/workspaces", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["description"] == payload["description"]
    assert data["owner_id"] == test_user.id
    assert "id" in data


@pytest.mark.asyncio
async def test_list_workspaces(async_client: AsyncClient, sample_workspace: Workspace, auth_headers: dict):
    response = await async_client.get("/api/v1/workspaces", headers=auth_headers)
    assert response.status_code == 200
    workspaces = response.json()
    assert isinstance(workspaces, list)
    assert any(ws["id"] == sample_workspace.id for ws in workspaces)


@pytest.mark.asyncio
async def test_get_workspace_by_id(async_client: AsyncClient, sample_workspace: Workspace, auth_headers: dict):
    response = await async_client.get(f"/api/v1/workspaces/{sample_workspace.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_workspace.id
    assert data["name"] == sample_workspace.name


@pytest.mark.asyncio
async def test_get_nonexistent_workspace_returns_404(async_client: AsyncClient, auth_headers: dict):
    response = await async_client.get("/api/v1/workspaces/non_existent_ws_999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_workspace_success(async_client: AsyncClient, sample_workspace: Workspace, auth_headers: dict):
    update_payload = {
        "name": "Advanced Quantum Kinetics",
        "description": "Updated description with new kinetic models",
        "is_archived": False,
    }
    response = await async_client.put(
        f"/api/v1/workspaces/{sample_workspace.id}",
        json=update_payload,
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Advanced Quantum Kinetics"
    assert data["description"] == "Updated description with new kinetic models"


@pytest.mark.asyncio
async def test_delete_workspace_by_owner_success(async_client: AsyncClient, sample_workspace: Workspace, auth_headers: dict):
    del_res = await async_client.delete(f"/api/v1/workspaces/{sample_workspace.id}", headers=auth_headers)
    assert del_res.status_code == 204

    # Subsequent fetch must return 404
    get_res = await async_client.get(f"/api/v1/workspaces/{sample_workspace.id}", headers=auth_headers)
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_unauthorized_user_cannot_access_workspace(
    async_client: AsyncClient,
    sample_workspace: Workspace,
    secondary_auth_headers: dict,
):
    response = await async_client.get(
        f"/api/v1/workspaces/{sample_workspace.id}",
        headers=secondary_auth_headers,
    )
    assert response.status_code == 403
    assert "do not have access" in response.json()["detail"]


@pytest.mark.asyncio
async def test_add_workspace_member_success(
    async_client: AsyncClient,
    sample_workspace: Workspace,
    secondary_user: User,
    auth_headers: dict,
    secondary_auth_headers: dict,
):
    member_payload = {
        "user_id": secondary_user.id,
        "role": "editor",
    }
    response = await async_client.post(
        f"/api/v1/workspaces/{sample_workspace.id}/members",
        json=member_payload,
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == secondary_user.id
    assert data["role"] == "editor"

    # Secondary user should now have access
    sec_get = await async_client.get(
        f"/api/v1/workspaces/{sample_workspace.id}",
        headers=secondary_auth_headers,
    )
    assert sec_get.status_code == 200


@pytest.mark.asyncio
async def test_add_duplicate_workspace_member_fails(
    async_client: AsyncClient,
    sample_workspace: Workspace,
    secondary_user: User,
    auth_headers: dict,
):
    member_payload = {"user_id": secondary_user.id, "role": "viewer"}
    res1 = await async_client.post(
        f"/api/v1/workspaces/{sample_workspace.id}/members",
        json=member_payload,
        headers=auth_headers,
    )
    assert res1.status_code == 201

    res2 = await async_client.post(
        f"/api/v1/workspaces/{sample_workspace.id}/members",
        json=member_payload,
        headers=auth_headers,
    )
    assert res2.status_code == 400
    assert "already a member" in res2.json()["detail"]
