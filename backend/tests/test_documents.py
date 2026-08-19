import io
import pytest
from httpx import AsyncClient
from tests.test_workspaces import create_user_and_login


@pytest.mark.asyncio
async def test_upload_document_success(async_client: AsyncClient):
    user, token = await create_user_and_login(async_client, "doc_owner@chemmind.org", "Doc Owner")
    headers = {"Authorization": f"Bearer {token}"}

    ws_res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "PDF Ingestion Lab"},
        headers=headers,
    )
    ws_id = ws_res.json()["id"]

    pdf_bytes = b"%PDF-1.4 sample PDF content for ChemMind research paper..."
    files = {"file": ("research_paper.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

    response = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/documents",
        files=files,
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "research_paper.pdf"
    assert data["status"] == "UPLOADED"
    assert data["workspace_id"] == ws_id
    assert data["doc_metadata"] is not None
    assert "checksum" in data["doc_metadata"]


@pytest.mark.asyncio
async def test_upload_invalid_extension_fails(async_client: AsyncClient):
    _, token = await create_user_and_login(async_client, "doc_user2@chemmind.org", "Doc User 2")
    headers = {"Authorization": f"Bearer {token}"}

    ws_res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "Invalid File Test Workspace"},
        headers=headers,
    )
    ws_id = ws_res.json()["id"]

    invalid_files = {"file": ("executable.exe", io.BytesIO(b"binary data"), "application/octet-stream")}
    response = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/documents",
        files=invalid_files,
        headers=headers,
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_and_get_document(async_client: AsyncClient):
    _, token = await create_user_and_login(async_client, "doc_lister@chemmind.org", "Lister User")
    headers = {"Authorization": f"Bearer {token}"}

    ws_res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "Listing Workspace"},
        headers=headers,
    )
    ws_id = ws_res.json()["id"]

    pdf_bytes = b"%PDF-1.4 test content..."
    files = {"file": ("paper_1.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    upload_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/documents",
        files=files,
        headers=headers,
    )
    doc_id = upload_res.json()["id"]

    list_res = await async_client.get(f"/api/v1/workspaces/{ws_id}/documents", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    get_res = await async_client.get(
        f"/api/v1/workspaces/{ws_id}/documents/{doc_id}",
        headers=headers,
    )
    assert get_res.status_code == 200
    assert get_res.json()["id"] == doc_id


@pytest.mark.asyncio
async def test_get_nonexistent_document_fails(async_client: AsyncClient):
    _, token = await create_user_and_login(async_client, "doc_404_user@chemmind.org", "Doc 404 User")
    headers = {"Authorization": f"Bearer {token}"}

    ws_res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "Empty Space"},
        headers=headers,
    )
    ws_id = ws_res.json()["id"]

    res = await async_client.get(
        f"/api/v1/workspaces/{ws_id}/documents/nonexistent-doc-id-99999",
        headers=headers,
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_document_fails(async_client: AsyncClient):
    _, token = await create_user_and_login(async_client, "del_404_user@chemmind.org", "Del 404 User")
    headers = {"Authorization": f"Bearer {token}"}

    ws_res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "Space for Del 404"},
        headers=headers,
    )
    ws_id = ws_res.json()["id"]

    res = await async_client.delete(
        f"/api/v1/workspaces/{ws_id}/documents/nonexistent-doc-id-99999",
        headers=headers,
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_delete_document(async_client: AsyncClient):
    _, token = await create_user_and_login(async_client, "doc_deleter@chemmind.org", "Deleter User")
    headers = {"Authorization": f"Bearer {token}"}

    ws_res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "Deletion Workspace"},
        headers=headers,
    )
    ws_id = ws_res.json()["id"]

    files = {"file": ("to_delete.pdf", io.BytesIO(b"%PDF-1.4 to delete..."), "application/pdf")}
    upload_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/documents",
        files=files,
        headers=headers,
    )
    doc_id = upload_res.json()["id"]

    del_res = await async_client.delete(
        f"/api/v1/workspaces/{ws_id}/documents/{doc_id}",
        headers=headers,
    )
    assert del_res.status_code == 204

    get_res = await async_client.get(
        f"/api/v1/workspaces/{ws_id}/documents/{doc_id}",
        headers=headers,
    )
    assert get_res.status_code == 404
