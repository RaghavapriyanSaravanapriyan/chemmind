import io
import pytest
from httpx import AsyncClient
from app.models.workspace import Workspace
from app.models.user import User


@pytest.mark.asyncio
async def test_path_traversal_prevention_in_file_upload(
    async_client: AsyncClient,
    sample_workspace: Workspace,
    auth_headers: dict,
    temp_storage_dir: str,
):
    # Attempt path traversal in filename
    traversal_filenames = [
        "../../../../etc/passwd.pdf",
        "..\\..\\..\\windows\\system32\\calc.pdf",
        "nested/../../../evil.pdf",
    ]

    for fname in traversal_filenames:
        files = {"file": (fname, io.BytesIO(b"%PDF-1.4 safe content"), "application/pdf")}
        response = await async_client.post(
            f"/api/v1/workspaces/{sample_workspace.id}/documents",
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == 201
        
        # Verify the file is saved strictly inside the workspace subdirectory
        storage_path = response.json()["storage_path"]
        assert sample_workspace.id in storage_path
        assert "etc" not in storage_path
        assert "system32" not in storage_path


@pytest.mark.asyncio
async def test_sql_injection_resilience_in_login(async_client: AsyncClient):
    sqli_payloads = [
        "' OR '1'='1",
        "admin' --",
        "test@chemmind.org'; DROP TABLE users; --",
        "' UNION SELECT * FROM users --",
    ]

    for sqli in sqli_payloads:
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": sqli, "password": "password123"},
        )
        # Should be rejected cleanly with 401 Unauthorized or 422 Validation Error, never 500 SQL syntax error
        assert response.status_code in [400, 401, 422]


@pytest.mark.asyncio
async def test_xss_payload_in_chat_prompt(
    async_client: AsyncClient,
    sample_workspace: Workspace,
    auth_headers: dict,
):
    conv_res = await async_client.post(
        f"/api/v1/workspaces/{sample_workspace.id}/conversations",
        json={"title": "XSS Test"},
        headers=auth_headers,
    )
    conv_id = conv_res.json()["id"]

    xss_prompt = "<script>alert('XSS')</script><img src=x onerror=alert(1)>"
    chat_res = await async_client.post(
        f"/api/v1/workspaces/{sample_workspace.id}/conversations/{conv_id}/chat",
        json={"prompt": xss_prompt},
        headers=auth_headers,
    )
    assert chat_res.status_code == 200
    # Response must be valid JSON without server error
    assert "content" in chat_res.json()


@pytest.mark.asyncio
async def test_role_escalation_viewer_cannot_modify_or_delete_workspace(
    async_client: AsyncClient,
    sample_workspace: Workspace,
    secondary_user: User,
    auth_headers: dict,
    secondary_auth_headers: dict,
):
    # Add secondary user as 'viewer'
    await async_client.post(
        f"/api/v1/workspaces/{sample_workspace.id}/members",
        json={"user_id": secondary_user.id, "role": "viewer"},
        headers=auth_headers,
    )

    # 1. Viewer tries to update workspace -> 403 Forbidden
    upd_res = await async_client.put(
        f"/api/v1/workspaces/{sample_workspace.id}",
        json={"name": "Hacked Title"},
        headers=secondary_auth_headers,
    )
    assert upd_res.status_code == 403

    # 2. Viewer tries to delete workspace -> 403 Forbidden
    del_res = await async_client.delete(
        f"/api/v1/workspaces/{sample_workspace.id}",
        headers=secondary_auth_headers,
    )
    assert del_res.status_code == 403
