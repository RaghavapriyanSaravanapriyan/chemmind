import pytest
from httpx import AsyncClient
from app.models.workspace import Workspace


@pytest.mark.asyncio
async def test_generate_workspace_quiz_success(
    async_client: AsyncClient,
    sample_workspace: Workspace,
    auth_headers: dict,
):
    payload = {
        "topic": "Organic Stereochemistry",
        "num_questions": 3,
    }
    response = await async_client.post(
        f"/api/v1/workspaces/{sample_workspace.id}/quizzes",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "quiz_id" in data
    assert "questions" in data
    assert data["workspace_id"] == sample_workspace.id

    for q in data["questions"]:
        assert "question_id" in q
        assert "question_text" in q
        assert "options" in q
        assert len(q["options"]) == 4
        assert "correct_answer" in q
        assert "explanation" in q


@pytest.mark.asyncio
async def test_generate_quiz_num_questions_bounds(
    async_client: AsyncClient,
    sample_workspace: Workspace,
    auth_headers: dict,
):
    # Test invalid num_questions (> 10)
    response = await async_client.post(
        f"/api/v1/workspaces/{sample_workspace.id}/quizzes",
        json={"num_questions": 25},
        headers=auth_headers,
    )
    assert response.status_code == 422  # Pydantic validation error (le=10)
