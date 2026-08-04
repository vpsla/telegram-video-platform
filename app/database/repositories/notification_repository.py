"""Notification repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.notification import Notification, NotificationType


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        body: str | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            body=body,
        )
        self._session.add(notification)
        await self._session.flush()
        return notification

    async def mark_sent(self, notification_id: int) -> None:
        notification = await self._session.get(Notification, notification_id)
        if notification is None:
            raise ValueError(f"Notification {notification_id} not found")
        notification.is_sent = True
        notification.error_message = None
        await self._session.flush()

    async def mark_failed(self, notification_id: int, error_message: str) -> None:
        notification = await self._session.get(Notification, notification_id)
        if notification is None:
            raise ValueError(f"Notification {notification_id} not found")
        notification.is_sent = False
        notification.error_message = error_message[:500]
        await self._session.flush()

    async def list_for_user(
        self, user_id: int, *, offset: int = 0, limit: int = 20
    ) -> list[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
