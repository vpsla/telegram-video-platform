"""
Video ORM model.

Represents one piece of media stored in the Telegram storage channel.
Per the spec: the bot never re-uploads — it only ever stores the
(channel_id, message_id) pair and later calls `bot.copy_message()` to
re-deliver the exact same file to end users.

A Video may or may not belong to a Series:
  - `episode` (one-to-one, nullable) links it into a series as a
    numbered episode.
  - If `episode` is None, it's a standalone video (e.g. a one-off clip)
    browsable directly, independent of any series.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Video(TimestampMixin, Base):
    __tablename__ = "videos"
    __table_args__ = (
        Index("ix_videos_channel_message", "channel_id", "message_id", unique=True),
        Index("ix_videos_category_id", "category_id"),
        Index("ix_videos_is_hidden", "is_hidden"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Telegram source-of-truth — never re-uploaded, only copied.
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    thumbnail_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )

    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    category: Mapped[Category | None] = relationship(lazy="raise")  # noqa: F821
    episode: Mapped[Episode | None] = relationship(  # noqa: F821
        back_populates="video", lazy="raise", uselist=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"Video(id={self.id}, channel_id={self.channel_id}, message_id={self.message_id})"
