"""Video repository."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.episode import Episode
from app.database.models.video import Video


class VideoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, video_id: int) -> Video | None:
        return await self._session.get(Video, video_id)

    async def get_by_channel_message(self, channel_id: int, message_id: int) -> Video | None:
        stmt = select(Video).where(Video.channel_id == channel_id, Video.message_id == message_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        channel_id: int,
        message_id: int,
        title: str,
        description: str | None = None,
        thumbnail_file_id: str | None = None,
        duration_seconds: int | None = None,
        file_size_bytes: int | None = None,
        category_id: int | None = None,
    ) -> Video:
        video = Video(
            channel_id=channel_id,
            message_id=message_id,
            title=title,
            description=description,
            thumbnail_file_id=thumbnail_file_id,
            duration_seconds=duration_seconds,
            file_size_bytes=file_size_bytes,
            category_id=category_id,
        )
        self._session.add(video)
        await self._session.flush()
        return video

    async def update(self, video_id: int, **fields: object) -> Video:
        video = await self.get_by_id(video_id)
        if video is None:
            raise ValueError(f"Video {video_id} not found")
        for key, value in fields.items():
            if value is not None and hasattr(video, key):
                setattr(video, key, value)
        await self._session.flush()
        return video

    async def set_hidden(self, video_id: int, *, hidden: bool) -> None:
        video = await self.get_by_id(video_id)
        if video is None:
            raise ValueError(f"Video {video_id} not found")
        video.is_hidden = hidden
        await self._session.flush()

    async def delete(self, video_id: int) -> None:
        video = await self.get_by_id(video_id)
        if video is None:
            raise ValueError(f"Video {video_id} not found")
        await self._session.delete(video)
        await self._session.flush()

    async def increment_view_count(self, video_id: int, delta: int = 1) -> None:
        video = await self.get_by_id(video_id)
        if video is None:
            raise ValueError(f"Video {video_id} not found")
        video.view_count += delta
        await self._session.flush()

    # --- Episode linking ---------------------------------------------------

    async def attach_as_episode(
        self,
        *,
        video_id: int,
        series_id: int,
        episode_number: int,
        title_override: str | None = None,
    ) -> Episode:
        """Attach an existing standalone Video to a Series as a numbered episode."""
        episode = Episode(
            video_id=video_id,
            series_id=series_id,
            episode_number=episode_number,
            title_override=title_override,
        )
        self._session.add(episode)
        await self._session.flush()
        return episode

    async def get_episode_by_video_id(self, video_id: int) -> Episode | None:
        stmt = select(Episode).where(Episode.video_id == video_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_episodes_for_series(self, series_id: int) -> list[Episode]:
        stmt = (
            select(Episode)
            .where(Episode.series_id == series_id)
            .options(selectinload(Episode.video))
            .order_by(Episode.episode_number)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_episode_by_series_and_number(
        self, series_id: int, episode_number: int
    ) -> Episode | None:
        stmt = (
            select(Episode)
            .where(Episode.series_id == series_id, Episode.episode_number == episode_number)
            .options(selectinload(Episode.video))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    # --- Listings ------------------------------------------------------------

    async def list_newest_standalone(self, *, offset: int = 0, limit: int = 20) -> list[Video]:
        """Videos not attached to any series ("video lẻ"), newest first."""
        stmt = (
            select(Video)
            .outerjoin(Episode, Episode.video_id == Video.id)
            .where(Video.is_hidden.is_(False), Episode.id.is_(None))
            .order_by(Video.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_total(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(Video))
        return result.scalar_one()
