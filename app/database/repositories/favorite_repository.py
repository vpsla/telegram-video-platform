"""Favorite repository."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.favorite import Favorite
from app.database.models.series import Series


class FavoriteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: int, series_id: int) -> Favorite | None:
        stmt = select(Favorite).where(Favorite.user_id == user_id, Favorite.series_id == series_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def is_following(self, user_id: int, series_id: int) -> bool:
        return await self.get(user_id, series_id) is not None

    async def add(self, user_id: int, series_id: int) -> Favorite:
        existing = await self.get(user_id, series_id)
        if existing is not None:
            return existing
        favorite = Favorite(user_id=user_id, series_id=series_id)
        self._session.add(favorite)
        await self._session.flush()
        return favorite

    async def remove(self, user_id: int, series_id: int) -> bool:
        favorite = await self.get(user_id, series_id)
        if favorite is None:
            return False
        await self._session.delete(favorite)
        await self._session.flush()
        return True

    async def list_for_user(
        self, user_id: int, *, offset: int = 0, limit: int = 20
    ) -> list[Favorite]:
        stmt = (
            select(Favorite)
            .where(Favorite.user_id == user_id)
            .options(selectinload(Favorite.series).selectinload(Series.category))
            .order_by(Favorite.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_for_user(self, user_id: int) -> int:
        stmt = select(func.count()).select_from(Favorite).where(Favorite.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def list_follower_user_ids(self, series_id: int) -> list[int]:
        """Used by the notification service (Phase 6) to fan out 'new
        episode' notifications to everyone following a series."""
        stmt = select(Favorite.user_id).where(Favorite.series_id == series_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
