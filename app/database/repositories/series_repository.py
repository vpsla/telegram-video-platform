"""Series repository."""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.series import Series


class SeriesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, series_id: int, *, with_category: bool = False) -> Series | None:
        if with_category:
            stmt = (
                select(Series).where(Series.id == series_id).options(selectinload(Series.category))
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        return await self._session.get(Series, series_id)

    async def get_by_slug(self, slug: str) -> Series | None:
        stmt = select(Series).where(Series.slug == slug)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        category_id: int,
        title: str,
        slug: str,
        description: str | None = None,
        author: str | None = None,
        thumbnail_file_id: str | None = None,
        tags: str | None = None,
    ) -> Series:
        series = Series(
            category_id=category_id,
            title=title,
            slug=slug,
            description=description,
            author=author,
            thumbnail_file_id=thumbnail_file_id,
            tags=tags,
        )
        self._session.add(series)
        await self._session.flush()
        return series

    async def update(self, series_id: int, **fields: object) -> Series:
        series = await self.get_by_id(series_id)
        if series is None:
            raise ValueError(f"Series {series_id} not found")
        for key, value in fields.items():
            if value is not None and hasattr(series, key):
                setattr(series, key, value)
        await self._session.flush()
        return series

    async def set_hidden(self, series_id: int, *, hidden: bool) -> None:
        series = await self.get_by_id(series_id)
        if series is None:
            raise ValueError(f"Series {series_id} not found")
        series.is_hidden = hidden
        await self._session.flush()

    async def delete(self, series_id: int) -> None:
        series = await self.get_by_id(series_id)
        if series is None:
            raise ValueError(f"Series {series_id} not found")
        await self._session.delete(series)
        await self._session.flush()

    async def increment_episode_count(self, series_id: int, delta: int = 1) -> None:
        series = await self.get_by_id(series_id)
        if series is None:
            raise ValueError(f"Series {series_id} not found")
        series.episode_count += delta
        await self._session.flush()

    async def increment_views(self, series_id: int, delta: int = 1) -> None:
        series = await self.get_by_id(series_id)
        if series is None:
            raise ValueError(f"Series {series_id} not found")
        series.total_views += delta
        await self._session.flush()

    async def increment_followers(self, series_id: int, delta: int = 1) -> None:
        series = await self.get_by_id(series_id)
        if series is None:
            raise ValueError(f"Series {series_id} not found")
        series.follower_count += delta
        await self._session.flush()

    def _visible_base_stmt(self):
        return select(Series).where(Series.is_hidden.is_(False))

    async def list_newest(self, *, offset: int = 0, limit: int = 20) -> list[Series]:
        stmt = (
            self._visible_base_stmt().order_by(Series.created_at.desc()).offset(offset).limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_featured(self, *, offset: int = 0, limit: int = 20) -> list[Series]:
        stmt = (
            self._visible_base_stmt()
            .where(Series.is_featured.is_(True))
            .order_by(Series.total_views.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_category(
        self, category_id: int, *, offset: int = 0, limit: int = 20
    ) -> list[Series]:
        stmt = (
            self._visible_base_stmt()
            .where(Series.category_id == category_id)
            .order_by(Series.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def search(self, query: str, *, offset: int = 0, limit: int = 20) -> list[Series]:
        """Approximate search across title, author, and tags.

        Uses simple case-insensitive substring matching (ILIKE), which
        Postgres (Supabase) supports natively. Good enough for the
        catalog sizes this platform targets; can be upgraded to
        full-text search (tsvector) later without changing the
        repository's public interface.
        """
        pattern = f"%{query}%"
        stmt = (
            self._visible_base_stmt()
            .where(
                or_(
                    Series.title.ilike(pattern),
                    Series.author.ilike(pattern),
                    Series.tags.ilike(pattern),
                )
            )
            .order_by(Series.total_views.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_total(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(Series))
        return result.scalar_one()
