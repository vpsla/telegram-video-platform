"""
WatchProgress ORM model.

Exactly one row per (user, video): tracks the last playback position
so the "Tiếp tục xem" (continue watching) feature can resume exactly
where the user left off. Upserted on every progress update, unlike
History which appends a new row per watch event.
"""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class WatchProgress(TimestampMixin, Base):
    __tablename__ = "watch_progress"
    __table_args__ = (
        Index("ix_watch_progress_user_video", "user_id", "video_id", unique=True),
        Index("ix_watch_progress_user_updated", "user_id", "updated_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    video_id: Mapped[int] = mapped_column(
        ForeignKey("videos.id", ondelete="CASCADE"), nullable=False
    )

    position_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped[User] = relationship(lazy="raise")  # noqa: F821
    video: Mapped[Video] = relationship(lazy="raise")  # noqa: F821

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"WatchProgress(user_id={self.user_id}, video_id={self.video_id}, "
            f"position={self.position_seconds}s)"
        )
