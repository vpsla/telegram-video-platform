from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.database.repositories.category_repository import CategoryRepository
from app.database.repositories.series_repository import SeriesRepository
from app.database.repositories.user_repository import UserRepository

# Must match the loop_scope of pg_engine/pg_session_factory fixtures.
pytestmark = pytest.mark.asyncio(loop_scope="module")


async def test_ilike_search_is_case_insensitive_on_postgres(
    pg_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Pins down ILIKE case-insensitivity against the real Postgres dialect."""
    async with pg_session_factory() as session:
        category_repo = CategoryRepository(session)
        series_repo = SeriesRepository(session)

        category = await category_repo.create(name="Tiên Hiệp", slug="pg-ilike-test")
        await series_repo.create(
            category_id=category.id,
            title="Phàm Nhân Tu Tiên",
            slug="pg-ilike-series",
            author="Vong Ngữ",
        )
        await session.commit()

        results_lower = await series_repo.search("phàm nhân")
        results_upper = await series_repo.search("PHÀM NHÂN")
        results_mixed = await series_repo.search("Phàm nhÂn")

    assert len(results_lower) >= 1
    assert len(results_upper) >= 1
    assert len(results_mixed) >= 1


async def test_bigint_telegram_id_roundtrip_on_postgres(
    pg_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Telegram user IDs can exceed int32 range — verify BigInteger stores correctly."""
    large_telegram_id = 5_123_456_789_012  # > 2^32

    async with pg_session_factory() as session:
        user_repo = UserRepository(session)
        user, created = await user_repo.get_or_create(telegram_id=large_telegram_id)
        await session.commit()

    assert created is True
    assert user.telegram_id == large_telegram_id

    async with pg_session_factory() as session:
        user_repo = UserRepository(session)
        reloaded = await user_repo.get_by_telegram_id(large_telegram_id)

    assert reloaded is not None
    assert reloaded.telegram_id == large_telegram_id
