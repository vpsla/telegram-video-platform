"""WatchProgress repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.watch_progress import WatchProgress


class WatchProgressRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: int, video_id: int) -> WatchProgress | None:
        stmt = select(WatchProgress).where(
            WatchProgress.user_id == user_id, WatchProgress.video_id == video_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        user_id: int,
        video_id: int,
        position_seconds: int,
        is_completed: bool = False,
    ) -> WatchProgress:
        progress = await self.get(user_id, video_id)
        if progress is None:
            progress = WatchProgress(
                user_id=user_id,
                video_id=video_id,
                position_seconds=position_seconds,
                is_completed=is_completed,
            )
            self._session.add(progress)
        else:
            progress.position_seconds = position_seconds
            progress.is_completed = is_completed
        await self._session.flush()
        return progress

    async def list_continue_watching(self, user_id: int, *, limit: int = 10) -> list[WatchProgress]:
        """Unfinished videos, most recently updated first."""
        stmt = (
            select(WatchProgress)
            .where(WatchProgress.user_id == user_id, WatchProgress.is_completed.is_(False))
            .options(selectinload(WatchProgress.video))
            .order_by(WatchProgress.updated_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, user_id: int, video_id: int) -> bool:
        progress = await self.get(user_id, video_id)
        if progress is None:
            return False
        await self._session.delete(progress)
        await self._session.flush()
        return True
