"""History repository."""

from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.history import History
from app.database.models.video import Video


class HistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(self, *, user_id: int, video_id: int) -> History:
        entry = History(user_id=user_id, video_id=video_id)
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def list_for_user(
        self, user_id: int, *, offset: int = 0, limit: int = 20
    ) -> list[History]:
        stmt = (
            select(History)
            .where(History.user_id == user_id)
            .options(selectinload(History.video))
            .order_by(History.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_for_user(self, user_id: int) -> int:
        stmt = select(func.count()).select_from(History).where(History.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def clear_for_user(self, user_id: int) -> int:
        stmt = delete(History).where(History.user_id == user_id)
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount or 0

    async def list_recently_watched_videos(self, user_id: int, *, limit: int = 10) -> list[Video]:
        """Distinct videos, most-recently-watched first — used for the
        'Tiếp tục xem' shelf alongside WatchProgress."""
        stmt = (
            select(Video)
            .join(History, History.video_id == Video.id)
            .where(History.user_id == user_id)
            .order_by(History.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        # de-duplicate while preserving order (a video may appear many times)
        seen: set[int] = set()
        videos: list[Video] = []
        for video in result.scalars().all():
            if video.id not in seen:
                seen.add(video.id)
                videos.append(video)
        return videos
