"""Shared pytest fixtures."""

from __future__ import annotations

import asyncio
import os

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "000000:TEST-TOKEN-NOT-REAL")
os.environ.setdefault("TELEGRAM_STORAGE_CHANNEL_ID", "-1001111111111")
os.environ.setdefault("TELEGRAM_WEBHOOK_BASE_URL", "https://example.com")
os.environ.setdefault("TELEGRAM_WEBHOOK_SECRET_TOKEN", "test-secret")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db"
)


@pytest.fixture(scope="session")
def event_loop():
    """Tạo event loop duy nhất cho session để fix lỗi 'different loop'."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def settings():
    from app.config.settings import get_settings

    get_settings.cache_clear()
    return get_settings()


@pytest.fixture
async def db_session():
    from app.database import models  # noqa: F401
    from app.database.base import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture(scope="session")
async def pg_engine():
    from app.database.base import Base

    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(db_url, pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def pg_session_factory(pg_engine):
    return async_sessionmaker(bind=pg_engine, expire_on_commit=False, autoflush=True)
