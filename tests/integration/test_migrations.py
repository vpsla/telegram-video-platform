from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

_EXPECTED_TABLES = {
    "users",
    "categories",
    "series",
    "videos",
    "episodes",
    "favorites",
    "history",
    "watch_progress",
    "settings",
    "notifications",
    "views",
    "alembic_version",
}


async def test_migration_chain_creates_all_tables(pg_engine: AsyncEngine) -> None:
    """The single most important deployment-readiness check: every
    migration from Phase 1 through Phase 6 applies cleanly, in order,
    against real Postgres — not just against SQLAlchemy's in-memory
    metadata (which the rest of the suite exercises via SQLite)."""
    async with pg_engine.connect() as conn:
        result = await conn.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        )
        tables = {row[0] for row in result}

    missing = _EXPECTED_TABLES - tables
    assert not missing, f"Migrations did not create expected tables: {missing}"


async def test_migration_chain_creates_expected_indexes(pg_engine: AsyncEngine) -> None:
    """Spot-check a handful of the Phase 6 optimization indexes to make
    sure they actually landed in the real database, not just declared
    on the SQLAlchemy model."""
    expected_indexes = {
        "ix_users_telegram_id",
        "ix_videos_channel_message",
        "ix_videos_category_id",
        "ix_videos_is_hidden",
        "ix_series_is_hidden",
        "ix_series_is_featured",
        "ix_views_video_created",
    }
    async with pg_engine.connect() as conn:
        result = await conn.execute(
            text("SELECT indexname FROM pg_indexes WHERE schemaname = 'public'")
        )
        indexes = {row[0] for row in result}

    missing = expected_indexes - indexes
    assert not missing, f"Expected indexes missing after migration: {missing}"
