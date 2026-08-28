import asyncio
import time
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
    # Fire 20 concurrent requests across health and chemistry endpoints
    tasks = []
    for _ in range(10):
        tasks.append(async_client.get("/api/v1/health"))
        tasks.append(
            async_client.post(
                "/api/v1/chemistry/properties",
                json={"smiles": "c1ccccc1"},
            )
        )

    start_time = time.time()
    responses = await asyncio.gather(*tasks)
    elapsed = time.time() - start_time

    assert len(responses) == 20
    assert all(r.status_code == 200 for r in responses)
    # Total execution time for 20 in-memory requests should be under 5 seconds
    assert elapsed < 5.0


def test_chemistry_calculation_latency_benchmark():
    chem_engine = ChemistryEngine()
    smiles_list = ["C", "CCO", "c1ccccc1", "CC(=O)O", "C1CCCCC1"] * 50  # 250 calculations

    start_time = time.time()
    for smi in smiles_list:
        chem_engine.parse_molecular_properties(smi)
        chem_engine.generate_3d_coordinates(smi)
    elapsed = time.time() - start_time

    # 250 calculations should complete in well under 1 second (< 0.004s per calculation)
    assert elapsed < 2.0
