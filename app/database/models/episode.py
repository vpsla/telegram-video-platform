"""
Episode ORM model.

Links a Series to a specific Video as a numbered episode. Kept as its
own table (rather than putting series_id/episode_number directly on
Video) so a Video can cleanly exist either as a standalone item or as
exactly one episode of one series, without nullable-FK ambiguity
spreading into Video itself.
"""

from __future__ import annotations

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Episode(TimestampMixin, Base):
    __tablename__ = "episodes"
    __table_args__ = (
        Index("ix_episodes_series_id", "series_id"),
        Index("ix_episodes_series_number", "series_id", "episode_number", unique=True),
        Index("ix_episodes_video_id", "video_id", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    series_id: Mapped[int] = mapped_column(
        ForeignKey("series.id", ondelete="CASCADE"), nullable=False
    )
    video_id: Mapped[int] = mapped_column(
        ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    episode_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title_override: Mapped[str | None] = mapped_column(
        String(255), nullable=True, doc="Optional per-episode title, e.g. 'Chương 12: ...'"
    )

    series: Mapped[Series] = relationship(back_populates="episodes", lazy="raise")  # noqa: F821
    video: Mapped[Video] = relationship(back_populates="episode", lazy="raise")  # noqa: F821

    def __repr__(self) -> str:  # pragma: no cover
        return f"Episode(id={self.id}, series_id={self.series_id}, number={self.episode_number})"
