from fastapi import APIRouter
from app.api.v1.endpoints import auth, conversations, documents, health, workspaces

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(workspaces.router, prefix="/workspaces", tags=["Workspaces"])
api_router.include_router(documents.router, prefix="/workspaces", tags=["Documents"])
api_router.include_router(conversations.router, prefix="/workspaces", tags=["Conversations"])
