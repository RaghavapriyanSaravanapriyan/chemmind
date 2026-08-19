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

    await async_client.post("/api/v1/workspaces", json={"name": "Workspace A"}, headers=headers)
    await async_client.post("/api/v1/workspaces", json={"name": "Workspace B"}, headers=headers)

    response = await async_client.get("/api/v1/workspaces", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_workspace_access_isolation(async_client: AsyncClient):
    _, token1 = await create_user_and_login(async_client, "user1@chemmind.org", "User One")
    res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "Private Project"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    ws_id = res.json()["id"]

    _, token2 = await create_user_and_login(async_client, "user2@chemmind.org", "User Two")
    get_res = await async_client.get(
        f"/api/v1/workspaces/{ws_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert get_res.status_code == 403


@pytest.mark.asyncio
async def test_add_member_and_access(async_client: AsyncClient):
    _, token1 = await create_user_and_login(async_client, "user_a@chemmind.org", "User A")
    res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "Shared Lab"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    ws_id = res.json()["id"]

    user2, token2 = await create_user_and_login(async_client, "user_b@chemmind.org", "User B")

    add_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"user_id": user2["id"], "role": "editor"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert add_res.status_code == 201

    get_res = await async_client.get(
        f"/api/v1/workspaces/{ws_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Shared Lab"


@pytest.mark.asyncio
async def test_add_duplicate_member_fails(async_client: AsyncClient):
    _, token1 = await create_user_and_login(async_client, "dup_owner@chemmind.org", "Dup Owner")
    ws_res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "Dup Member Lab"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    ws_id = ws_res.json()["id"]

    user2, _ = await create_user_and_login(async_client, "dup_target@chemmind.org", "Dup Target")

    # First add
    res1 = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"user_id": user2["id"], "role": "editor"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert res1.status_code == 201

    # Second add of same user
    res2 = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"user_id": user2["id"], "role": "editor"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert res2.status_code == 400
    assert "already a member" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_add_nonexistent_user_as_member_fails(async_client: AsyncClient):
    _, token = await create_user_and_login(async_client, "invalid_mem_owner@chemmind.org", "Mem Owner")
    ws_res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "Invalid Member Space"},
        headers={"Authorization": f"Bearer {token}"},
    )
    ws_id = ws_res.json()["id"]

    res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"user_id": "nonexistent-user-uuid-99999", "role": "editor"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_non_owner_delete_workspace_fails(async_client: AsyncClient):
    _, token1 = await create_user_and_login(async_client, "real_owner@chemmind.org", "Real Owner")
    ws_res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "Protected Space"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    ws_id = ws_res.json()["id"]

    user2, token2 = await create_user_and_login(async_client, "editor_user@chemmind.org", "Editor User")

    # Add user2 as editor
    await async_client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"user_id": user2["id"], "role": "editor"},
        headers={"Authorization": f"Bearer {token1}"},
    )

    # Editor tries to delete workspace
    del_res = await async_client.delete(
        f"/api/v1/workspaces/{ws_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert del_res.status_code == 403


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

    update_res = await async_client.put(
        f"/api/v1/workspaces/{ws_id}",
        json={"name": "Updated Workspace Name"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Updated Workspace Name"

    del_res = await async_client.delete(f"/api/v1/workspaces/{ws_id}", headers=headers)
    assert del_res.status_code == 204

    get_res = await async_client.get(f"/api/v1/workspaces/{ws_id}", headers=headers)
    assert get_res.status_code == 404
