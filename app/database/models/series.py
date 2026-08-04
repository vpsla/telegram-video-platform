"""
Series ORM model.

A "bộ truyện" (novel/story series) — groups multiple Episodes under one
title, cover, and category. Series-level denormalized counters
(episode_count, total_views) avoid expensive joins on every listing
page (Trang chủ, Video nổi bật, etc.).
"""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Series(TimestampMixin, Base):
    __tablename__ = "series"
    __table_args__ = (
        Index("ix_series_category_id", "category_id"),
        Index("ix_series_slug", "slug", unique=True),
        Index("ix_series_is_hidden", "is_hidden"),
        Index("ix_series_is_featured", "is_featured"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    thumbnail_file_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, doc="Telegram file_id of the cover thumbnail"
    )
    tags: Mapped[str | None] = mapped_column(
        String(500), nullable=True, doc="Comma-separated tags for search"
    )

    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Denormalized counters, maintained by the service layer whenever an
    # episode is added/removed or a view is recorded.
    episode_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    follower_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    category: Mapped[Category] = relationship(back_populates="series", lazy="raise")  # noqa: F821
    episodes: Mapped[list[Episode]] = relationship(  # noqa: F821
        back_populates="series", lazy="raise", order_by="Episode.episode_number"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"Series(id={self.id}, title={self.title!r})"
