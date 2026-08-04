"""View repository — write path is a single insert; read path powers
the statistics dashboard (time-series + top-N rankings)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.view import View


class ViewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(self, *, video_id: int, user_id: int | None) -> View:
        view = View(video_id=video_id, user_id=user_id)
        self._session.add(view)
        await self._session.flush()
        return view

    async def count_total(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(View))
        return result.scalar_one()

    async def count_since(self, since: datetime) -> int:
        stmt = select(func.count()).select_from(View).where(View.created_at >= since)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def views_per_day(self, since: datetime) -> list[tuple[datetime, int]]:
        """Returns (day, count) pairs for the "Lượt xem theo ngày" chart.

        Uses func.date() for cross-dialect (SQLite in tests, Postgres in
        production) day-bucketing — both support DATE() truncation of a
        timestamp column.
        """
        day_col = func.date(View.created_at)
        stmt = (
            select(day_col.label("day"), func.count().label("count"))
            .where(View.created_at >= since)
            .group_by(day_col)
            .order_by(day_col)
        )
        result = await self._session.execute(stmt)
        return [(row.day, row.count) for row in result.all()]

    async def top_video_ids(self, *, since: datetime, limit: int = 10) -> list[tuple[int, int]]:
        """Returns (video_id, view_count) pairs, most-viewed first, within
        the given time window."""
        stmt = (
            select(View.video_id, func.count().label("count"))
            .where(View.created_at >= since)
            .group_by(View.video_id)
            .order_by(func.count().desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [(row.video_id, row.count) for row in result.all()]

    async def top_viewer_user_ids(
        self, *, since: datetime, limit: int = 10
    ) -> list[tuple[int, int]]:
        """Returns (user_id, view_count) pairs for the most active
        viewers. Anonymous views (user_id is NULL) are excluded."""
        stmt = (
            select(View.user_id, func.count().label("count"))
            .where(View.created_at >= since, View.user_id.is_not(None))
            .group_by(View.user_id)
            .order_by(func.count().desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [(row.user_id, row.count) for row in result.all()]
