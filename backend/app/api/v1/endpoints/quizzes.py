from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.ai_gateway import ai_gateway
from ai.schemas.quiz import QuizGenerationRequest

router = APIRouter()


class QuizRequestSchema(BaseModel):
    topic: Optional[str] = Field(default="Molecular Chemistry & Bonding", description="Focus topic for quiz")
    num_questions: int = Field(default=3, ge=1, le=10, description="Number of questions to generate")
    document_ids: Optional[List[str]] = Field(default=None, description="Optional target document IDs")


@router.post(
    "/{workspace_id}/quizzes",
    status_code=status.HTTP_200_OK,
    summary="Generate Grounded Assessment Quiz from Workspace Documents",
)
async def generate_workspace_quiz(
    workspace_id: str,
    request: QuizRequestSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    if not ai_gateway.quiz_generator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Quiz Generator engine not available",
        )

    quiz_req = QuizGenerationRequest(
        workspace_id=workspace_id,
        topic=request.topic,
        num_questions=request.num_questions,
        document_ids=request.document_ids,
    )

    res = await ai_gateway.quiz_generator.generate_quiz(quiz_req)
    return res.model_dump()
