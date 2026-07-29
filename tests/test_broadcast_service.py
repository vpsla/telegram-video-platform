from __future__ import annotations

from unittest.mock import AsyncMock

from aiogram.exceptions import TelegramForbiddenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.user_repository import UserRepository
from app.services.broadcast_service import BroadcastService


def _make_forbidden_error() -> TelegramForbiddenError:
    # TelegramForbiddenError requires a method/message pair in aiogram 3.
    request = AsyncMock()
    request.method = "sendMessage"
    return TelegramForbiddenError(method=request, message="Forbidden: bot was blocked by the user")


async def test_broadcast_sends_to_all_users(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    for i in range(3):
        await user_repo.get_or_create(telegram_id=i + 1)

    service = BroadcastService(user_repo, batch_delay_seconds=0)
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=None)

    result = await service.broadcast_text(bot=bot, text="Hello!")

    assert result.total == 3
    assert result.sent == 3
    assert result.failed == 0
    assert bot.send_message.await_count == 3


async def test_broadcast_skips_banned_users(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    u1, _ = await user_repo.get_or_create(telegram_id=1)
    await user_repo.get_or_create(telegram_id=2)
    await user_repo.set_banned(u1.id, banned=True, reason="spam")

    service = BroadcastService(user_repo, batch_delay_seconds=0)
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=None)

    result = await service.broadcast_text(bot=bot, text="Hello!")

    assert result.sent == 1
    assert bot.send_message.await_count == 1


async def test_broadcast_handles_forbidden_error_per_user(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    await user_repo.get_or_create(telegram_id=100)
    await user_repo.get_or_create(telegram_id=200)

    service = BroadcastService(user_repo, batch_delay_seconds=0)
    bot = AsyncMock()
    bot.send_message = AsyncMock(side_effect=[_make_forbidden_error(), None])

    result = await service.broadcast_text(bot=bot, text="Hello!")

    assert result.sent == 1
    assert result.failed == 1
    assert 100 in result.blocked_user_ids


async def test_broadcast_empty_user_list(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    service = BroadcastService(user_repo, batch_delay_seconds=0)
    bot = AsyncMock()

    result = await service.broadcast_text(bot=bot, text="Hello!")

    assert result.total == 0
    assert result.sent == 0
    bot.send_message.assert_not_awaited()
