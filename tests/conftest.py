"""Shared pytest fixtures."""

from __future__ import annotations

import os

import pytest

# Set required env vars before any app module is imported, since
# AppSettings() is instantiated at import time in app.main.
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "000000:TEST-TOKEN-NOT-REAL")
os.environ.setdefault("TELEGRAM_STORAGE_CHANNEL_ID", "-1001111111111")
os.environ.setdefault("TELEGRAM_WEBHOOK_BASE_URL", "https://example.com")
os.environ.setdefault("TELEGRAM_WEBHOOK_SECRET_TOKEN", "test-secret")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db"
)


@pytest.fixture
def settings():
    from app.config.settings import get_settings

    get_settings.cache_clear()
    return get_settings()


@pytest.fixture
async def db_session():
    """A fresh in-memory SQLite async session per test.

    Engine is created AND used within the same async fixture — everything
    runs in the same event loop that pytest-asyncio provides for this test
    function, so there is no "attached to a different loop" risk.

    SQLite stands in for Supabase Postgres in unit tests: fast, no network,
    no external service required. Postgres-specific behavior is covered by
    tests/integration/ which run against a real Postgres instance in CI.
    """
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.database import models  # noqa: F401  (populates Base.metadata)
    from app.database.base import Base

    # Create engine inside the fixture (same event loop as the test).
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        # aiosqlite does not support multi-threaded sharing; check_same_thread
        # is already False by default in SQLAlchemy's aiosqlite dialect.
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with session_factory() as session:
        yield session
        # Always rollback at the end so each test starts with a clean slate.
        await session.rollback()

    # Dispose the engine after the session is fully closed.
    await engine.dispose()
