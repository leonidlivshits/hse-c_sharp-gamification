# tests/conftest.py
import os, sys, asyncio
from pathlib import Path
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine, AsyncSession
from httpx import AsyncClient, ASGITransport

# add project root so `import app` работает
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.db.session import Base
from app.main import app

# для CI/локал тестов: по умолчанию sqlite in-memory
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")


@pytest.fixture(scope="session")
async def async_engine() -> AsyncEngine:
    engine = create_async_engine(TEST_DATABASE_URL, future=True, echo=False)
    # создаём схему один раз
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


# Алиасы/совместимость с тестами, которые ждут fixture 'engine'
@pytest.fixture(scope="session")
async def engine(async_engine: AsyncEngine) -> AsyncEngine:
    return async_engine


@pytest.fixture()
async def session(async_engine: AsyncEngine) -> AsyncSession:
    """
    Простая per-test сессия. По завершении теста делаем rollback,
    чтобы не сохранять состояние между тестами.
    """
    async_session = async_sessionmaker(async_engine, expire_on_commit=False)
    async with async_session() as s:
        yield s
        # откат: если тест что-то закоммитил, откатим изменения
        try:
            await s.rollback()
        except Exception:
            pass


# alias для тестов, которые используют имя 'db'
@pytest.fixture()
async def db(session: AsyncSession):
    yield session


@pytest.fixture()
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
