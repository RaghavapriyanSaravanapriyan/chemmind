from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.ai_gateway import ai_gateway
from ai.schemas.reasoning import MultiDocAnalysisRequest

router = APIRouter()


class MultiDocRequestSchema(BaseModel):
    query_text: str = Field(..., description="Comparative synthesis query text")
    document_ids: List[str] = Field(..., min_items=1, description="Target document IDs to cross-examine")


@router.post(
    "/{workspace_id}/reasoning/multi-doc",
    status_code=status.HTTP_200_OK,
    summary="Cross-examine Multiple Papers and Detect Discrepancies",
)
async def analyze_multi_documents(
    workspace_id: str,
    request: MultiDocRequestSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    if not ai_gateway.multi_doc_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Multi-Doc Reasoning Engine not available",
        )

    req = MultiDocAnalysisRequest(
        workspace_id=workspace_id,
        query_text=request.query_text,
        document_ids=request.document_ids,
    )

    res = await ai_gateway.multi_doc_engine.analyze(req)
    return res.model_dump()
