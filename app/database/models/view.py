"""
View ORM model.

An append-only, system-facing view-event log — distinct from History
(Phase 4), which is user-facing and can be cleared by the user via
"Xóa lịch sử". Views must survive a History clear, since dashboards
("Lượt xem theo ngày", "Top video") need a complete, tamper-proof
record regardless of what the user does to their own history.

Kept intentionally lean (just the FKs + timestamp) since this table is
write-heavy (one insert per playback) and read via aggregate queries
(COUNT/GROUP BY), never joined for per-row detail.
"""

from __future__ import annotations

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class View(TimestampMixin, Base):
    __tablename__ = "views"
    __table_args__ = (
        Index("ix_views_video_created", "video_id", "created_at"),
        Index("ix_views_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    video_id: Mapped[int] = mapped_column(
        ForeignKey("videos.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="Nullable so a user-deletion never blocks/cascades away historical stats",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"View(video_id={self.video_id}, user_id={self.user_id})"
