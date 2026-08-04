"""
Category ORM model.

Flat category list (no nested subcategories in this phase — the spec
lists "Quản lý thể loại" as a single admin function, not a taxonomy
tree). `slug` is used for clean callback_data and future deep-linking.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Category(TimestampMixin, Base):
    __tablename__ = "categories"
    __table_args__ = (Index("ix_categories_slug", "slug", unique=True),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    icon_emoji: Mapped[str | None] = mapped_column(String(8), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    series: Mapped[list[Series]] = relationship(  # noqa: F821
        back_populates="category", lazy="raise"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"Category(id={self.id}, slug={self.slug!r})"
