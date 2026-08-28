import io
import pytest
from httpx import AsyncClient
from app.models.workspace import Workspace


@pytest.mark.asyncio
async def test_upload_document_success(
    async_client: AsyncClient,
    sample_workspace: Workspace,
    auth_headers: dict,
    temp_storage_dir: str,
):
    pdf_content = b"%PDF-1.4 ... Fake PDF document content for chemical paper ..."
    files = {"file": ("catalysis_paper.pdf", io.BytesIO(pdf_content), "application/pdf")}

    response = await async_client.post(
        f"/api/v1/workspaces/{sample_workspace.id}/documents",
        files=files,
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "catalysis_paper.pdf"
    assert data["file_size"] == len(pdf_content)
    assert data["status"] == "UPLOADED"
    assert "id" in data


@pytest.mark.asyncio
async def test_upload_unsupported_file_extension_fails(
    async_client: AsyncClient,
    sample_workspace: Workspace,
    auth_headers: dict,
    temp_storage_dir: str,
):
    files = {"file": ("malicious_script.exe", io.BytesIO(b"executable content"), "application/octet-stream")}

    response = await async_client.post(
        f"/api/v1/workspaces/{sample_workspace.id}/documents",
        files=files,
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_workspace_documents(
    async_client: AsyncClient,
    sample_workspace: Workspace,
    auth_headers: dict,
    temp_storage_dir: str,
):
    pdf_content = b"%PDF-1.4 paper content"
    files = {"file": ("paper_1.pdf", io.BytesIO(pdf_content), "application/pdf")}
    await async_client.post(
        f"/api/v1/workspaces/{sample_workspace.id}/documents",
        files=files,
        headers=auth_headers,
    )

    response = await async_client.get(
        f"/api/v1/workspaces/{sample_workspace.id}/documents",
        headers=auth_headers,
    )
    assert response.status_code == 200
    docs = response.json()
    assert isinstance(docs, list)
    assert len(docs) >= 1
    assert any(d["filename"] == "paper_1.pdf" for d in docs)


@pytest.mark.asyncio
async def test_get_document_by_id(
    async_client: AsyncClient,
    sample_workspace: Workspace,
    auth_headers: dict,
    temp_storage_dir: str,
):
    pdf_content = b"%PDF-1.4 sample content"
    files = {"file": ("specific_doc.pdf", io.BytesIO(pdf_content), "application/pdf")}
    upload_res = await async_client.post(
        f"/api/v1/workspaces/{sample_workspace.id}/documents",
        files=files,
        headers=auth_headers,
    )
    doc_id = upload_res.json()["id"]

    response = await async_client.get(
        f"/api/v1/workspaces/{sample_workspace.id}/documents/{doc_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == doc_id
    assert data["filename"] == "specific_doc.pdf"


@pytest.mark.asyncio
async def test_delete_document_success(
    async_client: AsyncClient,
    sample_workspace: Workspace,
    auth_headers: dict,
    temp_storage_dir: str,
):
    files = {"file": ("to_delete.pdf", io.BytesIO(b"%PDF-1.4 delete me"), "application/pdf")}
    upload_res = await async_client.post(
        f"/api/v1/workspaces/{sample_workspace.id}/documents",
        files=files,
        headers=auth_headers,
    )
    doc_id = upload_res.json()["id"]

    del_res = await async_client.delete(
        f"/api/v1/workspaces/{sample_workspace.id}/documents/{doc_id}",
        headers=auth_headers,
    )
    assert del_res.status_code == 204

    # Verification: document no longer in database
    get_res = await async_client.get(
        f"/api/v1/workspaces/{sample_workspace.id}/documents/{doc_id}",
        headers=auth_headers,
    )
    assert get_res.status_code == 404
