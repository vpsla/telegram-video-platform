from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.user_repository import UserRepository
from app.services.admin_user_service import AdminUserService, UserNotFoundError


async def test_ban_and_unban_user(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    service = AdminUserService(user_repo)

    user, _ = await user_repo.get_or_create(telegram_id=1)
    await service.ban_user(user.id, reason="spam")

    reloaded = await user_repo.get_by_id(user.id)
    assert reloaded is not None
    assert reloaded.is_banned is True
    assert reloaded.ban_reason == "spam"

    await service.unban_user(user.id)
    reloaded_again = await user_repo.get_by_id(user.id)
    assert reloaded_again is not None
    assert reloaded_again.is_banned is False


async def test_ban_unknown_user_raises(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    service = AdminUserService(user_repo)
    with pytest.raises(UserNotFoundError):
        await service.ban_user(99999, reason="x")


async def test_grant_and_revoke_vip(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    service = AdminUserService(user_repo)

    user, _ = await user_repo.get_or_create(telegram_id=2)
    await service.grant_vip(user.id)

    reloaded = await user_repo.get_by_id(user.id)
    assert reloaded is not None
    assert reloaded.is_currently_vip is True

    await service.revoke_vip(user.id)
    reloaded_again = await user_repo.get_by_id(user.id)
    assert reloaded_again is not None
    assert reloaded_again.is_currently_vip is False


async def test_find_by_telegram_id(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    service = AdminUserService(user_repo)
    await user_repo.get_or_create(telegram_id=777)

    found = await service.find_by_telegram_id(777)
    assert found is not None

    not_found = await service.find_by_telegram_id(888)
    assert not_found is None


async def test_list_users(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    service = AdminUserService(user_repo)
    for i in range(3):
        await user_repo.get_or_create(telegram_id=i + 1)

    users = await service.list_users(limit=2)
    assert len(users) == 2
