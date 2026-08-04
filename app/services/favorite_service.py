"""
Favorite service.

Wraps FavoriteRepository so that following/unfollowing a series always
keeps Series.follower_count (added in Phase 3) in sync — the counter
must never drift from the actual row count in `favorites`.
"""

from __future__ import annotations

from app.database.models.favorite import Favorite
from app.database.repositories.favorite_repository import FavoriteRepository
from app.database.repositories.series_repository import SeriesRepository


class SeriesNotFoundError(Exception):
    pass


class FavoriteService:
    def __init__(self, favorite_repo: FavoriteRepository, series_repo: SeriesRepository) -> None:
        self._favorite_repo = favorite_repo
        self._series_repo = series_repo

    async def follow(self, *, user_id: int, series_id: int) -> Favorite:
        series = await self._series_repo.get_by_id(series_id)
        if series is None:
            raise SeriesNotFoundError(f"Series {series_id} not found")

        if await self._favorite_repo.is_following(user_id, series_id):
            return await self._favorite_repo.get(user_id, series_id)  # type: ignore[return-value]

        favorite = await self._favorite_repo.add(user_id, series_id)
        await self._series_repo.increment_followers(series_id, delta=1)
        return favorite

    async def unfollow(self, *, user_id: int, series_id: int) -> bool:
        removed = await self._favorite_repo.remove(user_id, series_id)
        if removed:
            await self._series_repo.increment_followers(series_id, delta=-1)
        return removed

    async def toggle(self, *, user_id: int, series_id: int) -> bool:
        """Returns the new following state (True = now following)."""
        if await self._favorite_repo.is_following(user_id, series_id):
            await self.unfollow(user_id=user_id, series_id=series_id)
            return False
        await self.follow(user_id=user_id, series_id=series_id)
        return True

    async def is_following(self, user_id: int, series_id: int) -> bool:
        return await self._favorite_repo.is_following(user_id, series_id)

    async def list_for_user(self, user_id: int, *, offset: int = 0, limit: int = 20):
        return await self._favorite_repo.list_for_user(user_id, offset=offset, limit=limit)
