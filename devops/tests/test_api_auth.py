from datetime import timedelta
import pytest
from httpx import AsyncClient
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_auth_register_success(async_client: AsyncClient):
    payload = {
        "email": "dr_feynman@chemmind.org",
        "password": "QuantumElectrodynamics123!",
        "full_name": "Richard Feynman",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["full_name"] == payload["full_name"]
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_auth_register_duplicate_email_fails(async_client: AsyncClient):
    payload = {
        "email": "unique_scientist@chemmind.org",
        "password": "Password123!",
        "full_name": "Unique Chemist",
    }
    res1 = await async_client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = await async_client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_auth_login_success(async_client: AsyncClient):
    reg_payload = {
        "email": "roentgen@chemmind.org",
        "password": "XRaysDiscovery1895!",
        "full_name": "Wilhelm Roentgen",
    }
    await async_client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "email": reg_payload["email"],
        "password": reg_payload["password"],
    }
    response = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_auth_login_invalid_password(async_client: AsyncClient):
    reg_payload = {
        "email": "mendel@chemmind.org",
        "password": "GeneticsRules123!",
        "full_name": "Gregor Mendel",
    }
    await async_client.post("/api/v1/auth/register", json=reg_payload)

    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": reg_payload["email"], "password": "WrongPassword!"},
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_auth_login_nonexistent_email(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@chemmind.org", "password": "AnyPassword123!"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_get_me_authenticated(async_client: AsyncClient, test_user, auth_headers: dict):
    response = await async_client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["id"] == test_user.id


@pytest.mark.asyncio
async def test_auth_get_me_invalid_token(async_client: AsyncClient):
    headers = {"Authorization": "Bearer invalid_bearer_token"}
    response = await async_client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_get_me_expired_token(async_client: AsyncClient):
    expired_token = create_access_token(
        subject="some_user_id",
        expires_delta=timedelta(seconds=-10),
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = await async_client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
