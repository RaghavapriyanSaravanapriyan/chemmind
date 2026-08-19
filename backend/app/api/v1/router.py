from fastapi import APIRouter
from app.api.v1.endpoints import auth, documents, health, workspaces

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(workspaces.router, prefix="/workspaces", tags=["Workspaces"])
api_router.include_router(documents.router, prefix="/workspaces", tags=["Documents"])
