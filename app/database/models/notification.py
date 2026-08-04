"""
Notification ORM model.

Records notifications sent (or queued) to a user — new-episode alerts
for followed series, and admin broadcasts. Kept as a durable log so
"Nhận thông báo tập mới" has an audit trail and so a failed broadcast
send can be identified and retried without re-sending to everyone.
"""

from __future__ import annotations

from enum import StrEnum

from sqlalchemy import Boolean, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class NotificationType(StrEnum):
    NEW_EPISODE = "new_episode"
    BROADCAST = "broadcast"
    SYSTEM = "system"


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_user_created", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, native_enum=False, length=20), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)

    user: Mapped[User] = relationship(lazy="raise")  # noqa: F821

    def __repr__(self) -> str:  # pragma: no cover
        return f"Notification(id={self.id}, user_id={self.user_id}, type={self.notification_type})"
