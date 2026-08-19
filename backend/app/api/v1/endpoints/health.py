from typing import Any, Dict
from fastapi import APIRouter
from app.core.config import settings
from app.core.database import check_db_health

router = APIRouter()


@router.get("/health", response_model=Dict[str, Any], summary="Health Check")
async def health_check() -> Dict[str, Any]:
    db_connected = await check_db_health()
    return {
        "status": "ok" if db_connected else "degraded",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "database": "connected" if db_connected else "disconnected",
    }
