import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Tuple
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure repo root and backend are in sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.base import Base
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestAsyncSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(
        id="user_test_123",
        email="testchemist@chemmind.org",
        full_name="Dr. Marie Curie",
        hashed_password=get_password_hash("TestPassword123!"),
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def secondary_user(db_session: AsyncSession) -> User:
    user = User(
        id="user_test_456",
        email="colleague@chemmind.org",
        full_name="Dr. Linus Pauling",
        hashed_password=get_password_hash("ColleaguePass123!"),
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict:
    token = create_access_token(subject=test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def secondary_auth_headers(secondary_user: User) -> dict:
    token = create_access_token(subject=secondary_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def sample_workspace(db_session: AsyncSession, test_user: User) -> Workspace:
    ws = Workspace(
        id="ws_sample_001",
        name="Quantum Kinetics & Catalysis",
        description="Workspace investigating transition metal catalysis mechanisms",
        owner_id=test_user.id,
        is_archived=False,
    )
    db_session.add(ws)
    await db_session.flush()

    member = WorkspaceMember(
        workspace_id=ws.id,
        user_id=test_user.id,
        role="owner",
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(ws)
    return ws


@pytest.fixture
def temp_storage_dir(tmp_path) -> str:
    storage_path = tmp_path / "uploads"
    storage_path.mkdir(parents=True, exist_ok=True)
    original_storage = settings.STORAGE_DIR
    settings.STORAGE_DIR = str(storage_path)
    yield str(storage_path)
    settings.STORAGE_DIR = original_storage
