import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_chemist_research_workflow(
    async_client: AsyncClient,
    temp_storage_dir: str,
):
    # ── Step 1: Register User ──
    user_email = "e2e_chemist@chemmind.org"
    user_pass = "ComplexChemistPass123!"
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": user_email, "password": user_pass, "full_name": "E2E Researcher"},
    )
    assert reg_res.status_code == 201

    # ── Step 2: Login & Obtain JWT Token ──
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": user_email, "password": user_pass},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # ── Step 3: Create Research Workspace ──
    ws_res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "Total Synthesis of Taxol", "description": "Natural product synthesis strategies"},
        headers=headers,
    )
    assert ws_res.status_code == 201
    ws_id = ws_res.json()["id"]

    # ── Step 4: Upload Research Document ──
    pdf_file = {"file": ("taxol_synthesis.pdf", io.BytesIO(b"%PDF-1.4 Taxol paper text..."), "application/pdf")}
    doc_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/documents",
        files=pdf_file,
        headers=headers,
    )
    assert doc_res.status_code == 201
    doc_id = doc_res.json()["id"]

    # ── Step 5: Create Conversation ──
    conv_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/conversations",
        json={"title": "Taxol Ring Closure Discussion"},
        headers=headers,
    )
    assert conv_res.status_code == 201
    conv_id = conv_res.json()["id"]

    # ── Step 6: Ask RAG Copilot Question ──
    chat_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/conversations/{conv_id}/chat",
        json={"prompt": "What reagents were used for the oxetane ring construction?", "selected_document_ids": [doc_id]},
        headers=headers,
    )
    assert chat_res.status_code == 200
    assert len(chat_res.json()["content"]) > 0

    # ── Step 7: Generate Grounded Quiz Assessment ──
    quiz_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/quizzes",
        json={"topic": "Taxol Core Construction", "num_questions": 2},
        headers=headers,
    )
    assert quiz_res.status_code == 200
    assert len(quiz_res.json()["questions"]) == 2

    # ── Step 8: Compute 3D Chemistry Coordinates ──
    chem_res = await async_client.post(
        "/api/v1/chemistry/3d",
        json={"smiles": "benzene"},
    )
    assert chem_res.status_code == 200
    assert len(chem_res.json()["coordinates_3d"]) >= 6

    # ── Step 9: Verify Usage & Quotas ──
    usage_res = await async_client.get(
        f"/api/v1/workspaces/{ws_id}/usage",
        headers=headers,
    )
    assert usage_res.status_code == 200
    usage_data = usage_res.json()
    assert usage_data["documents_count"] == 1
    assert usage_data["ai_requests_count"] >= 1

    # ── Step 10: Delete Workspace & Verify Cascade ──
    del_res = await async_client.delete(
        f"/api/v1/workspaces/{ws_id}",
        headers=headers,
    )
    assert del_res.status_code == 204

    # Workspace no longer exists
    check_res = await async_client.get(f"/api/v1/workspaces/{ws_id}", headers=headers)
    assert check_res.status_code == 404
