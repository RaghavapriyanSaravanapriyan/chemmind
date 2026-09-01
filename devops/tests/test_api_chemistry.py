import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chemistry_properties_smiles_ethanol(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/chemistry/properties",
        json={"smiles": "CCO"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["smiles"] == "CCO"
    assert data["is_valid_smiles"] is True
    assert data["molecular_weight"] > 40.0
    assert "C" in data["chemical_formula"]


@pytest.mark.asyncio
async def test_chemistry_properties_named_compounds(async_client: AsyncClient):
    compounds = ["methane", "water", "benzene", "ethanol"]
    for name in compounds:
        response = await async_client.post(
            "/api/v1/chemistry/properties",
            json={"smiles": name},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid_smiles"] is True
        assert data["molecular_weight"] > 0


@pytest.mark.asyncio
async def test_chemistry_properties_invalid_smiles(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/chemistry/properties",
        json={"smiles": "$$invalid$$"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid_smiles"] is False
    assert data["molecular_weight"] == 0.0


@pytest.mark.asyncio
async def test_chemistry_3d_coordinates_benzene(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/chemistry/3d",
        json={"smiles": "benzene"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["smiles"] == "c1ccccc1"
    assert len(data["atoms"]) >= 1
    assert len(data["coordinates_3d"]) == len(data["atoms"])
    for coord in data["coordinates_3d"]:
        assert len(coord) == 3


@pytest.mark.asyncio
async def test_chemistry_3d_coordinates_methane(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/chemistry/3d",
        json={"smiles": "methane"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["atoms"]) >= 1
