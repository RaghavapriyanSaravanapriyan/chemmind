from fastapi import APIRouter
from app.api.v1.endpoints import auth, chat, chemistry, conversations, documents, health, quizzes, reasoning, usage, workspaces

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(workspaces.router, prefix="/workspaces", tags=["Workspaces"])
api_router.include_router(documents.router, prefix="/workspaces", tags=["Documents"])
api_router.include_router(conversations.router, prefix="/workspaces", tags=["Conversations"])
api_router.include_router(chat.router, prefix="/workspaces", tags=["AI Chat"])
api_router.include_router(usage.router, prefix="/workspaces", tags=["Usage & Limits"])
api_router.include_router(chemistry.router, prefix="/chemistry", tags=["Chemistry Engine"])
api_router.include_router(quizzes.router, prefix="/workspaces", tags=["Quiz Assessment"])
api_router.include_router(reasoning.router, prefix="/workspaces", tags=["Multi-Doc Reasoning"])

