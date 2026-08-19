import pytest
from httpx import AsyncClient


async def create_user_and_login(async_client: AsyncClient, email: str, name: str) -> tuple[dict, str]:
    password = "TestPassword123!"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": name},
    )
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_res.json()["access_token"]
    me_res = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    user_data = me_res.json()
    return user_data, token


@pytest.mark.asyncio
async def test_create_workspace_success(async_client: AsyncClient):
    user, token = await create_user_and_login(async_client, "owner1@chemmind.org", "Owner One")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "name": "Quantum Chemistry Research",
        "description": "Workspace for DFT calculations and paper analysis.",
    }
    response = await async_client.post("/api/v1/workspaces", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["description"] == payload["description"]
    assert data["owner_id"] == user["id"]
    assert data["is_archived"] is False


@pytest.mark.asyncio
async def test_list_workspaces(async_client: AsyncClient):
    _, token = await create_user_and_login(async_client, "owner2@chemmind.org", "Owner Two")
    headers = {"Authorization": f"Bearer {token}"}

    # Create two workspaces
    await async_client.post("/api/v1/workspaces", json={"name": "Workspace A"}, headers=headers)
    await async_client.post("/api/v1/workspaces", json={"name": "Workspace B"}, headers=headers)

    response = await async_client.get("/api/v1/workspaces", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_workspace_access_isolation(async_client: AsyncClient):
    # User 1 creates workspace
    _, token1 = await create_user_and_login(async_client, "user1@chemmind.org", "User One")
    res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "Private Project"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    ws_id = res.json()["id"]

    # User 2 tries to access User 1's workspace
    _, token2 = await create_user_and_login(async_client, "user2@chemmind.org", "User Two")
    get_res = await async_client.get(
        f"/api/v1/workspaces/{ws_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert get_res.status_code == 403


@pytest.mark.asyncio
async def test_add_member_and_access(async_client: AsyncClient):
    # User 1 creates workspace
    _, token1 = await create_user_and_login(async_client, "user_a@chemmind.org", "User A")
    res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "Shared Lab"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    ws_id = res.json()["id"]

    # User 2 registers
    user2, token2 = await create_user_and_login(async_client, "user_b@chemmind.org", "User B")

    # User 1 adds User 2 as member
    add_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"user_id": user2["id"], "role": "editor"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert add_res.status_code == 201

    # User 2 can now access workspace
    get_res = await async_client.get(
        f"/api/v1/workspaces/{ws_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Shared Lab"


@pytest.mark.asyncio
async def test_update_and_delete_workspace(async_client: AsyncClient):
    _, token = await create_user_and_login(async_client, "deleter@chemmind.org", "Deleter User")
    headers = {"Authorization": f"Bearer {token}"}

    create_res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "Temporary Workspace"},
        headers=headers,
    )
    ws_id = create_res.json()["id"]

    # Update
    update_res = await async_client.put(
        f"/api/v1/workspaces/{ws_id}",
        json={"name": "Updated Workspace Name"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Updated Workspace Name"

    # Delete
    del_res = await async_client.delete(f"/api/v1/workspaces/{ws_id}", headers=headers)
    assert del_res.status_code == 204

    # Verify deleted
    get_res = await async_client.get(f"/api/v1/workspaces/{ws_id}", headers=headers)
    assert get_res.status_code == 404
