"""
User repository.

All database access for User lives here. Services and handlers never
issue raw SQLAlchemy queries against User directly — this is what lets
Phase 5 (admin panel) and Phase 6 (statistics) reuse the exact same
query logic instead of duplicating it.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: int) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        language_code: str | None = None,
        is_admin: bool = False,
    ) -> User:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
            is_admin=is_admin,
        )
        self._session.add(user)
        await self._session.flush()
        return user

    async def get_or_create(
        self,
        *,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        language_code: str | None = None,
        is_admin: bool = False,
    ) -> tuple[User, bool]:
        """Return (user, created). Also refreshes profile fields + last_active_at
        on every call for existing users, since this runs on every update."""
        user = await self.get_by_telegram_id(telegram_id)
        if user is not None:
            changed = False
            if user.username != username:
                user.username = username
                changed = True
            if user.first_name != first_name:
                user.first_name = first_name
                changed = True
            if user.last_name != last_name:
                user.last_name = last_name
                changed = True
            if user.language_code != language_code:
                user.language_code = language_code
                changed = True
            user.last_active_at = datetime.now(UTC)
            if changed:
                await self._session.flush()
            return user, False

        user = await self.create(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
            is_admin=is_admin,
        )
        user.last_active_at = datetime.now(UTC)
        await self._session.flush()
        return user, True

    async def set_banned(self, user_id: int, *, banned: bool, reason: str | None = None) -> None:
        user = await self.get_by_id(user_id)
        if user is None:
            raise ValueError(f"User {user_id} not found")
        user.is_banned = banned
        user.ban_reason = reason if banned else None
        await self._session.flush()

    async def set_vip(self, user_id: int, *, vip: bool, expires_at: datetime | None = None) -> None:
        user = await self.get_by_id(user_id)
        if user is None:
            raise ValueError(f"User {user_id} not found")
        user.is_vip = vip
        user.vip_expires_at = expires_at if vip else None
        await self._session.flush()

    async def add_watch_seconds(self, user_id: int, seconds: int) -> None:
        user = await self.get_by_id(user_id)
        if user is None:
            raise ValueError(f"User {user_id} not found")
        user.total_watch_seconds += seconds
        await self._session.flush()

    async def count_total(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(User))
        return result.scalar_one()

    async def count_new_since(self, since: datetime) -> int:
        stmt = select(func.count()).select_from(User).where(User.created_at >= since)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def list_paginated(
        self, *, offset: int = 0, limit: int = 20, banned_only: bool = False
    ) -> list[User]:
        stmt = select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
        if banned_only:
            stmt = stmt.where(User.is_banned.is_(True))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
