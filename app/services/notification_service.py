"""
Notification dispatch service.

Bridges FavoriteRepository (who follows what) with NotificationRepository
(durable log) and Telegram's send_message API. Kept separate from
VideoService/FavoriteService so "attach a new episode" doesn't need to
know about Telegram delivery, and so a failed send for one follower
never blocks notifying the rest.
"""

from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError

from app.database.models.notification import NotificationType
from app.database.repositories.favorite_repository import FavoriteRepository
from app.database.repositories.notification_repository import NotificationRepository
from app.database.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(
        self,
        notification_repo: NotificationRepository,
        favorite_repo: FavoriteRepository,
        user_repo: UserRepository,
    ) -> None:
        self._notification_repo = notification_repo
        self._favorite_repo = favorite_repo
        self._user_repo = user_repo

    async def notify_new_episode(
        self,
        *,
        bot: Bot,
        series_id: int,
        series_title: str,
        episode_number: int,
    ) -> int:
        """Create + send a "new episode" notification to every follower
        of `series_id`. Returns the number of followers successfully
        notified. Each follower is isolated: one failed send (blocked
        bot, deleted account) is logged on that Notification row and
        does not stop the rest from being notified.
        """
        follower_ids = await self._favorite_repo.list_follower_user_ids(series_id)
        title = f"Tập mới: {series_title}"
        body = f"{series_title} vừa ra tập {episode_number}. Xem ngay!"

        sent_count = 0
        for user_id in follower_ids:
            user = await self._user_repo.get_by_id(user_id)
            if user is None or user.is_banned:
                continue

            notification = await self._notification_repo.create(
                user_id=user_id,
                notification_type=NotificationType.NEW_EPISODE,
                title=title,
                body=body,
            )
            try:
                await bot.send_message(chat_id=user.telegram_id, text=f"🔔 {title}\n\n{body}")
                await self._notification_repo.mark_sent(notification.id)
                sent_count += 1
            except TelegramForbiddenError:
                await self._notification_repo.mark_failed(notification.id, "User blocked bot")
            except Exception as exc:
                logger.exception("Failed to notify user_id=%s of new episode", user_id)
                await self._notification_repo.mark_failed(notification.id, str(exc)[:500])

        return sent_count
