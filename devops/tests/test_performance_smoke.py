import asyncio
import time
from unittest.mock import patch
import pytest
from httpx import AsyncClient
from ai.chemistry.engine import ChemistryEngine
from app.models.workspace import Workspace


@pytest.mark.asyncio
async def test_concurrent_api_requests_smoke(
    async_client: AsyncClient,
    sample_workspace: Workspace,
    auth_headers: dict,
):
    # Fire 10 concurrent requests across health and chemistry endpoints
    tasks = []
    for _ in range(5):
        tasks.append(async_client.get("/api/v1/health"))
        tasks.append(
            async_client.post(
                "/api/v1/chemistry/properties",
                json={"smiles": "CCO"},
            )
        )

    start_time = time.time()
    responses = await asyncio.gather(*tasks)
    elapsed = time.time() - start_time

    assert len(responses) == 10
    assert all(r.status_code == 200 for r in responses)
    assert elapsed < 10.0


def test_chemistry_calculation_latency_benchmark():
    chem_engine = ChemistryEngine()
    smiles_list = ["C", "CCO", "c1ccccc1", "CC(=O)O", "C1CCCCC1"] * 10  # 50 calculations

    start_time = time.time()
    for smi in smiles_list:
        chem_engine.parse_molecular_properties(smi)
        chem_engine.generate_3d_coordinates(smi)
    elapsed = time.time() - start_time

    # 50 calculations should complete in well under 5 seconds
    assert elapsed < 5.0
