"""
Favorite ORM model.

Represents a user "following" a Series ("Theo dõi bộ truyện" /
"Yêu thích" in the spec). One row per (user, series) pair — favoriting
is series-level, not per-episode, since users follow stories to get
notified about new episodes (see Notification model, Phase 4/6).
"""

from __future__ import annotations

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Favorite(TimestampMixin, Base):
    __tablename__ = "favorites"
    __table_args__ = (
        Index("ix_favorites_user_series", "user_id", "series_id", unique=True),
        Index("ix_favorites_series_id", "series_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    series_id: Mapped[int] = mapped_column(
        ForeignKey("series.id", ondelete="CASCADE"), nullable=False
    )

    user: Mapped[User] = relationship(lazy="raise")  # noqa: F821
    series: Mapped[Series] = relationship(lazy="raise")  # noqa: F821

    def __repr__(self) -> str:  # pragma: no cover
        return f"Favorite(user_id={self.user_id}, series_id={self.series_id})"
