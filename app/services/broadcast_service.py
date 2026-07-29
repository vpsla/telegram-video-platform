"""
Broadcast service.

Sends a message to every registered user. Each send is isolated: one
user's failure (blocked bot, deactivated account, etc.) must never
abort the batch for everyone else. Results are tallied so the admin
gets a clear sent/failed count instead of a silent partial failure.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

from app.database.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

# Telegram allows roughly 30 messages/second across all chats; batching
# with a small delay between chunks keeps us comfortably under that
# without needing a dedicated task queue for Phase 5.
_BATCH_SIZE = 25
_BATCH_DELAY_SECONDS = 1.0


@dataclass
class BroadcastResult:
    total: int
    sent: int
    failed: int
    blocked_user_ids: list[int]


class BroadcastService:
    def __init__(
        self,
        user_repo: UserRepository,
        *,
        batch_size: int = _BATCH_SIZE,
        batch_delay_seconds: float = _BATCH_DELAY_SECONDS,
    ) -> None:
        self._user_repo = user_repo
        self._batch_size = batch_size
        self._batch_delay_seconds = batch_delay_seconds

    async def broadcast_text(self, *, bot: Bot, text: str) -> BroadcastResult:
        sent = 0
        failed = 0
        blocked_user_ids: list[int] = []

        offset = 0
        batch_size = self._batch_size
        total = await self._user_repo.count_total()

        while True:
            users = await self._user_repo.list_paginated(offset=offset, limit=batch_size)
            if not users:
                break

            for user in users:
                if user.is_banned:
                    continue
                try:
                    await bot.send_message(chat_id=user.telegram_id, text=text)
                    sent += 1
                except TelegramForbiddenError:
                    # User blocked the bot or deleted their account.
                    blocked_user_ids.append(user.telegram_id)
                    failed += 1
                except TelegramRetryAfter as exc:
                    logger.warning("Rate limited, sleeping %.1fs", exc.retry_after)
                    await asyncio.sleep(exc.retry_after)
                    try:
                        await bot.send_message(chat_id=user.telegram_id, text=text)
                        sent += 1
                    except Exception:
                        logger.exception(
                            "Broadcast retry failed for telegram_id=%s", user.telegram_id
                        )
                        failed += 1
                except Exception:
                    logger.exception("Broadcast failed for telegram_id=%s", user.telegram_id)
                    failed += 1

            offset += batch_size
            if self._batch_delay_seconds > 0:
                await asyncio.sleep(self._batch_delay_seconds)

        return BroadcastResult(
            total=total, sent=sent, failed=failed, blocked_user_ids=blocked_user_ids
        )
