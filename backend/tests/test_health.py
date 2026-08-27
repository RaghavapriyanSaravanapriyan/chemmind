import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_health_check(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["service"] == "ChemMind Backend API"
    assert data["environment"] == "development"


@pytest.mark.asyncio
async def test_api_v1_health_check(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["service"] == "ChemMind Backend API"
