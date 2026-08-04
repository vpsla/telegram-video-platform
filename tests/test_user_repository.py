from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.user_repository import UserRepository


async def test_get_or_create_creates_new_user(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)

    user, created = await repo.get_or_create(telegram_id=111, username="dora", first_name="Dora")

    assert created is True
    assert user.telegram_id == 111
    assert user.username == "dora"
    assert user.is_admin is False
    assert user.last_active_at is not None


async def test_get_or_create_returns_existing_user(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)

    first, created_first = await repo.get_or_create(telegram_id=222, username="old_name")
    second, created_second = await repo.get_or_create(telegram_id=222, username="new_name")

    assert created_first is True
    assert created_second is False
    assert first.id == second.id
    assert second.username == "new_name"  # profile refreshed in place


async def test_get_by_telegram_id_not_found_returns_none(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)
    result = await repo.get_by_telegram_id(999999)
    assert result is None


async def test_set_banned(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)
    user, _ = await repo.get_or_create(telegram_id=333)

    await repo.set_banned(user.id, banned=True, reason="spam")
    reloaded = await repo.get_by_id(user.id)
    assert reloaded is not None
    assert reloaded.is_banned is True
    assert reloaded.ban_reason == "spam"

    await repo.set_banned(user.id, banned=False)
    reloaded_again = await repo.get_by_id(user.id)
    assert reloaded_again is not None
    assert reloaded_again.is_banned is False
    assert reloaded_again.ban_reason is None


async def test_set_vip_permanent_and_expiring(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)
    user, _ = await repo.get_or_create(telegram_id=444)

    await repo.set_vip(user.id, vip=True)
    reloaded = await repo.get_by_id(user.id)
    assert reloaded is not None
    assert reloaded.is_currently_vip is True

    past = datetime.now(UTC) - timedelta(days=1)
    await repo.set_vip(user.id, vip=True, expires_at=past)
    reloaded_expired = await repo.get_by_id(user.id)
    assert reloaded_expired is not None
    assert reloaded_expired.is_currently_vip is False


async def test_set_vip_or_ban_raises_for_unknown_user(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)
    with pytest.raises(ValueError):
        await repo.set_banned(99999, banned=True)
    with pytest.raises(ValueError):
        await repo.set_vip(99999, vip=True)


async def test_add_watch_seconds_accumulates(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)
    user, _ = await repo.get_or_create(telegram_id=555)

    await repo.add_watch_seconds(user.id, 120)
    await repo.add_watch_seconds(user.id, 30)

    reloaded = await repo.get_by_id(user.id)
    assert reloaded is not None
    assert reloaded.total_watch_seconds == 150


async def test_count_total_and_new_since(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)
    await repo.get_or_create(telegram_id=1)
    await repo.get_or_create(telegram_id=2)
    await repo.get_or_create(telegram_id=3)

    assert await repo.count_total() == 3

    future_cutoff = datetime.now(UTC) + timedelta(days=1)
    assert await repo.count_new_since(future_cutoff) == 0

    past_cutoff = datetime.now(UTC) - timedelta(days=1)
    assert await repo.count_new_since(past_cutoff) == 3


async def test_list_paginated_and_banned_only_filter(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)
    u1, _ = await repo.get_or_create(telegram_id=10)
    await repo.get_or_create(telegram_id=20)
    await repo.get_or_create(telegram_id=30)
    await repo.set_banned(u1.id, banned=True)

    page = await repo.list_paginated(offset=0, limit=2)
    assert len(page) == 2

    banned = await repo.list_paginated(banned_only=True)
    assert len(banned) == 1
    assert banned[0].telegram_id == 10
