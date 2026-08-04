"""
User middleware.

Runs after DatabaseMiddleware (needs data["session"]). Extracts the
Telegram `from_user` off whatever event type comes through (Message,
CallbackQuery, etc.), get-or-creates the corresponding User row, and
injects it into `data["user"]` for every downstream handler.

Also short-circuits banned users here, once, instead of every handler
having to remember to check `user.is_banned`.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update
from aiogram.types import User as TgUser

from app.config.settings import AppSettings
from app.database.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


def _extract_from_user(event: TelegramObject) -> TgUser | None:
    if isinstance(event, Update):
        inner = event.event
        return _extract_from_user(inner) if inner else None
    if isinstance(event, Message):
        return event.from_user
    if isinstance(event, CallbackQuery):
        return event.from_user
    # Fallback for any other update type carrying `from_user`
    return getattr(event, "from_user", None)


class UserMiddleware(BaseMiddleware):
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = _extract_from_user(event)
        if tg_user is None or tg_user.is_bot:
            return await handler(event, data)

        session = data["session"]
        repo = UserRepository(session)

        user, created = await repo.get_or_create(
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
            language_code=tg_user.language_code,
            is_admin=tg_user.id in self._settings.admin_ids,
        )

        if created:
            logger.info("New user registered: telegram_id=%s", tg_user.id)

        if user.is_banned:
            logger.info("Blocked update from banned user telegram_id=%s", tg_user.id)
            if isinstance(event, Message):
                await event.answer("🚫 Tài khoản của bạn đã bị khóa.")
            elif isinstance(event, CallbackQuery):
                await event.answer("🚫 Tài khoản của bạn đã bị khóa.", show_alert=True)
            return None

        data["user"] = user
        data["user_repo"] = repo
        return await handler(event, data)
