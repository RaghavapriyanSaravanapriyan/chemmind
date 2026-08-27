from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials and credentials.credentials:
        token = credentials.credentials
        payload = decode_access_token(token)

        if not payload or "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = payload["sub"]
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
        except Exception:
            user = None

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user",
            )
        return user

    # Default fallback user for unauthenticated local development
    try:
        result = await db.execute(select(User).where(User.email == "dev@chemmind.local"))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                id="dev_user_001",
                email="dev@chemmind.local",
                full_name="Local ChemMind Researcher",
                hashed_password="dev_hashed_password",
                is_active=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user
    except Exception:
        return User(
            id="dev_user_001",
            email="dev@chemmind.local",
            full_name="Local ChemMind Researcher",
            hashed_password="dev_hashed_password",
            is_active=True,
        )



async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user

