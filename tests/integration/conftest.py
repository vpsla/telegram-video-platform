"""Fixtures for Postgres-backed integration tests.

All async fixtures here use loop_scope="module" so that the engine,
session factory, and individual test sessions share exactly one event
loop per test module. This is the correct pattern for pytest-asyncio
>= 0.23 when using module-scoped async resources with asyncpg, which
is very strict about connection objects not crossing loop boundaries.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _database_url() -> str:
    return os.environ.get("DATABASE_URL", "")


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def pg_engine():
    """Module-scoped Postgres engine with all migrations applied.

    Skips the whole module when DATABASE_URL isn't a Postgres/asyncpg URL
    or the server isn't reachable — lets the suite run harmlessly on a
    laptop without Docker and meaningfully in CI where the service is up.
    """
    url = _database_url()
    if "asyncpg" not in url:
        pytest.skip("DATABASE_URL is not configured for Postgres (asyncpg) — skipping")

    engine = create_async_engine(
        url,
        connect_args={"statement_cache_size": 0},
        pool_pre_ping=True,
    )
    try:
        async with engine.connect() as conn:
            await conn.close()
    except Exception as exc:  # noqa: BLE001
        await engine.dispose()
        pytest.skip(f"Postgres not reachable at {url!r}: {exc}")

    # Reset schema then apply all migrations end-to-end on real Postgres.
    env = os.environ.copy()
    subprocess.run(
        [sys.executable, "-m", "alembic", "downgrade", "base"],
        cwd=_PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=_PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        await engine.dispose()
        pytest.fail(f"alembic upgrade head failed:\n{result.stdout}\n{result.stderr}")

    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def pg_session_factory(pg_engine: AsyncEngine):
    return async_sessionmaker(
        bind=pg_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


@pytest_asyncio.fixture(scope="function", loop_scope="module")
async def pg_session(pg_session_factory: async_sessionmaker[AsyncSession]):
    """Function-scoped session, but runs in the module's shared event loop.

    Rolls back after every test so each test starts with a clean state
    without having to recreate the expensive module-scoped engine.
    """
    async with pg_session_factory() as session:
        yield session
        await session.rollback()
