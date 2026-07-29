"""Fixtures for Postgres-backed integration tests."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _database_url() -> str:
    return os.environ.get("DATABASE_URL", "")


# pytest-asyncio >= 0.23 uses `loop_scope` on the fixture decorator instead
# of overriding the deprecated `event_loop` fixture. Setting loop_scope="module"
# ensures the engine is created and used within the same event loop for all
# tests in the module, fixing "Future attached to a different loop" errors
# that occur when asyncpg connections span different event loops.


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
    )
    try:
        async with engine.connect():
            pass
    except Exception as exc:
        await engine.dispose()
        pytest.skip(f"Postgres not reachable at {url!r}: {exc}")

    # Reset schema then apply all migrations — this proves the full
    # migration chain (Phase 1-6) works end-to-end on real Postgres.
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
    return async_sessionmaker(bind=pg_engine, expire_on_commit=False)


@pytest_asyncio.fixture(loop_scope="module")
async def pg_session(pg_session_factory):
    async with pg_session_factory() as session:
        yield session
        await session.rollback()
