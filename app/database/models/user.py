"""
User ORM model.

Represents a Telegram end-user of the platform. `telegram_id` is the
natural key we receive on every update; `id` is the internal surrogate
PK used by all foreign keys elsewhere (videos favorites, history, etc.)
so that we're never coupled to Telegram's ID format in the rest of the
schema.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (Index("ix_users_telegram_id", "telegram_id", unique=True),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language_code: Mapped[str | None] = mapped_column(String(8), nullable=True)

    # Access control
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_vip: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    vip_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ban_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Engagement stats (denormalized counters, updated by services —
    # avoids expensive COUNT() aggregations on every dashboard load)
    total_watch_seconds: Mapped[int] = mapped_column(default=0, nullable=False)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debug convenience only
        return f"User(id={self.id}, telegram_id={self.telegram_id}, username={self.username!r})"

    @property
    def display_name(self) -> str:
        if self.username:
            return f"@{self.username}"
        name = " ".join(filter(None, [self.first_name, self.last_name]))
        return name or f"User#{self.telegram_id}"

    @property
    def is_currently_vip(self) -> bool:
        """VIP flag alone isn't enough — must also check expiry."""
        if not self.is_vip:
            return False
        if self.vip_expires_at is None:
            return True  # permanent VIP
        from datetime import UTC
        from datetime import datetime as dt

        return self.vip_expires_at > dt.now(UTC)
