"""
Database session middleware.

Opens one transaction-scoped AsyncSession per incoming Telegram update
and makes it available to every handler as `data["session"]`.
Commits on success, rolls back on any unhandled exception — this
mirrors the session_scope() context manager in app/database/engine.py
but adapted to aiogram's middleware signature.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker

logger = logging.getLogger(__name__)


class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._session_factory = session_factory

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with self._session_factory() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                logger.exception("Unhandled error while processing update; rolled back session")
                raise
