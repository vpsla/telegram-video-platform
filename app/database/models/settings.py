"""
Settings ORM model.

Simple key-value store for runtime-configurable app settings that
admins can change without redeploying (e.g. maintenance mode,
registration open/closed, broadcast rate limit). Distinct from
app/config/settings.py (AppSettings), which is deployment-time
configuration from environment variables.
"""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class Settings(TimestampMixin, Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(String(2000), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"Settings(key={self.key!r}, value={self.value!r})"
