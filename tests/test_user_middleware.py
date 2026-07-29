from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from aiogram.types import Chat, Message
from aiogram.types import User as TgUser

from app.config.settings import AppSettings
from app.database.repositories.user_repository import UserRepository
from app.middlewares.user import UserMiddleware


def _make_message(user_id: int, username: str = "tester") -> Message:
    tg_user = TgUser(id=user_id, is_bot=False, first_name="Test", username=username)
    chat = Chat(id=user_id, type="private")
    message = Message(
        message_id=1,
        date=0,  # type: ignore[arg-type]
        chat=chat,
        from_user=tg_user,
        text="/start",
    )
    return message


async def test_middleware_injects_user_and_calls_handler(db_session, settings: AppSettings) -> None:
    middleware = UserMiddleware(settings)
    handler = AsyncMock(return_value="handled")
    message = _make_message(12345)

    data = {"session": db_session}
    result = await middleware(handler, message, data)

    assert result == "handled"
    assert "user" in data
    assert data["user"].telegram_id == 12345
    handler.assert_awaited_once()


async def test_middleware_marks_admin_from_settings(
    db_session, settings: AppSettings, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(type(settings), "admin_ids", property(lambda self: [777]))
    middleware = UserMiddleware(settings)
    handler = AsyncMock(return_value=None)
    message = _make_message(777)

    data = {"session": db_session}
    await middleware(handler, message, data)

    assert data["user"].is_admin is True


async def test_middleware_blocks_banned_user(
    db_session, settings: AppSettings, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Pre-create and ban the user before the update arrives.
    repo = UserRepository(db_session)
    user, _ = await repo.get_or_create(telegram_id=555)
    await repo.set_banned(user.id, banned=True, reason="test")

    answer_mock = AsyncMock()
    monkeypatch.setattr(Message, "answer", answer_mock)

    middleware = UserMiddleware(settings)
    handler = AsyncMock(return_value="should not be called")
    message = _make_message(555)

    data = {"session": db_session}
    result = await middleware(handler, message, data)

    handler.assert_not_awaited()
    answer_mock.assert_awaited_once()
    assert result is None
