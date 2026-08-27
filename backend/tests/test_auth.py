from datetime import timedelta
import pytest
from httpx import AsyncClient
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_register_user_success(async_client: AsyncClient):
    payload = {
        "email": "testuser@chemmind.org",
        "password": "SecretPassword123!",
        "full_name": "Test Chemist",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["full_name"] == payload["full_name"]
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email_fails(async_client: AsyncClient):
    payload = {
        "email": "duplicate@chemmind.org",
        "password": "Password123!",
        "full_name": "Duplicate User",
    }
    res1 = await async_client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = await async_client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient):
    reg_payload = {
        "email": "loginuser@chemmind.org",
        "password": "MySecurePassword123",
        "full_name": "Login User",
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
async def test_login_invalid_password_fails(async_client: AsyncClient):
    reg_payload = {
        "email": "wrongpwd@chemmind.org",
        "password": "CorrectPassword123",
        "full_name": "Wrong Pwd User",
    }
    await async_client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "email": reg_payload["email"],
        "password": "WrongPassword123",
    }
    response = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_email_fails(async_client: AsyncClient):
    login_payload = {
        "email": "nonexistent@chemmind.org",
        "password": "AnyPassword123",
    }
    response = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_me_authenticated(async_client: AsyncClient):
    reg_payload = {
        "email": "meuser@chemmind.org",
        "password": "MePassword123",
        "full_name": "Me User",
    }
    await async_client.post("/api/v1/auth/register", json=reg_payload)

    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": reg_payload["email"], "password": reg_payload["password"]},
    )
    token = login_res.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_res = await async_client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    user_data = me_res.json()
    assert user_data["email"] == reg_payload["email"]
    assert user_data["full_name"] == reg_payload["full_name"]


@pytest.mark.asyncio
async def test_get_me_invalid_token_fails(async_client: AsyncClient):
    headers = {"Authorization": "Bearer invalid.jwt.token"}
    me_res = await async_client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 401


@pytest.mark.asyncio
async def test_get_me_expired_token_fails(async_client: AsyncClient):
    expired_token = create_access_token(
        subject="some-user-id",
        expires_delta=timedelta(seconds=-10),
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    me_res = await async_client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 401
