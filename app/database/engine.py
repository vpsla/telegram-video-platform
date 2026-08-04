"""
Async SQLAlchemy engine and session factory.

Session-per-request pattern: get_session() is an async generator meant
to be used as a dependency (FastAPI Depends, or manually in aiogram
middlewares from Phase 2 onward).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import AppSettings


def create_engine(settings: AppSettings) -> AsyncEngine:
    return create_async_engine(
        settings.database.url.get_secret_value(),
        pool_size=settings.database.pool_size,
        max_overflow=settings.database.max_overflow,
        pool_timeout=settings.database.pool_timeout,
        echo=settings.database.echo,
        pool_pre_ping=True,  # guards against Supabase closing idle connections
        pool_recycle=1800,  # recycle connections every 30 min, avoids stale sockets
        connect_args={
            # Supabase's "Connection Pooling" endpoint runs PgBouncer in
            # transaction mode, which does not support server-side
            # prepared statements. asyncpg prepares statements by
            # default, causing intermittent
            # "prepared statement ... already exists" errors under load.
            # Disabling the statement cache trades a small per-query
            # parse cost for correctness against the pooler. Has no
            # effect (and is harmless) against a direct connection or
            # local/CI Postgres.
            "statement_cache_size": 0,
        },
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


@asynccontextmanager
async def session_scope(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional scope: commits on success, rolls back on error."""
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
