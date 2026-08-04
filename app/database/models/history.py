"""
History ORM model.

An append-only log: one row per watch event. Powers the "Lịch sử"
(history) screen, which shows a reverse-chronological feed of what the
user has watched — distinct from WatchProgress, which tracks only the
single latest resume position per (user, video).
"""

from __future__ import annotations

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class History(TimestampMixin, Base):
    __tablename__ = "history"
    __table_args__ = (
        Index("ix_history_user_created", "user_id", "created_at"),
        Index("ix_history_video_id", "video_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    video_id: Mapped[int] = mapped_column(
        ForeignKey("videos.id", ondelete="CASCADE"), nullable=False
    )

    user: Mapped[User] = relationship(lazy="raise")  # noqa: F821
    video: Mapped[Video] = relationship(lazy="raise")  # noqa: F821

    def __repr__(self) -> str:  # pragma: no cover
        return f"History(user_id={self.user_id}, video_id={self.video_id})"
