"""
Statistics service.

Coordinates ViewRepository (time-series/top-N aggregates) with
VideoRepository/SeriesRepository/UserRepository to resolve raw IDs into
display-ready objects. Kept separate from any single repository since
these queries fundamentally span multiple tables.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.database.models.series import Series
from app.database.models.user import User
from app.database.models.video import Video
from app.database.repositories.series_repository import SeriesRepository
from app.database.repositories.user_repository import UserRepository
from app.database.repositories.video_repository import VideoRepository
from app.database.repositories.view_repository import ViewRepository


@dataclass
class DailyViewCount:
    day: str
    count: int


@dataclass
class VideoRanking:
    video: Video
    view_count: int


@dataclass
class ViewerRanking:
    user: User
    view_count: int


@dataclass
class DashboardStats:
    total_users: int
    new_users_7d: int
    total_series: int
    total_videos: int
    total_views: int
    views_7d: int


class StatisticsService:
    def __init__(
        self,
        view_repo: ViewRepository,
        video_repo: VideoRepository,
        series_repo: SeriesRepository,
        user_repo: UserRepository,
    ) -> None:
        self._view_repo = view_repo
        self._video_repo = video_repo
        self._series_repo = series_repo
        self._user_repo = user_repo

    async def get_dashboard_stats(self, *, recent_days: int = 7) -> DashboardStats:
        since = datetime.now(UTC) - timedelta(days=recent_days)
        return DashboardStats(
            total_users=await self._user_repo.count_total(),
            new_users_7d=await self._user_repo.count_new_since(since),
            total_series=await self._series_repo.count_total(),
            total_videos=await self._video_repo.count_total(),
            total_views=await self._view_repo.count_total(),
            views_7d=await self._view_repo.count_since(since),
        )

    async def get_views_per_day(self, *, days: int = 7) -> list[DailyViewCount]:
        since = datetime.now(UTC) - timedelta(days=days)
        raw = await self._view_repo.views_per_day(since)
        return [DailyViewCount(day=str(day), count=count) for day, count in raw]

    async def get_top_videos(self, *, days: int = 7, limit: int = 10) -> list[VideoRanking]:
        since = datetime.now(UTC) - timedelta(days=days)
        raw = await self._view_repo.top_video_ids(since=since, limit=limit)

        rankings: list[VideoRanking] = []
        for video_id, count in raw:
            video = await self._video_repo.get_by_id(video_id)
            if video is not None:
                rankings.append(VideoRanking(video=video, view_count=count))
        return rankings

    async def get_top_series(self, *, limit: int = 10) -> list[Series]:
        """Top series by the denormalized Series.total_views counter
        (already maintained by VideoService on every episode view) —
        cheaper than re-aggregating Views for a value read far more
        often than it changes. Featured series are surfaced first;
        the remainder is filled by total_views ordering."""
        featured = await self._series_repo.list_featured(limit=limit)
        if len(featured) >= limit:
            return featured[:limit]

        newest = await self._series_repo.list_newest(limit=limit * 3)
        by_views = sorted(newest, key=lambda s: s.total_views, reverse=True)

        combined: list[Series] = list(featured)
        seen_ids = {s.id for s in featured}
        for series in by_views:
            if series.id not in seen_ids:
                combined.append(series)
                seen_ids.add(series.id)
            if len(combined) >= limit:
                break
        return combined[:limit]

    async def get_top_viewers(self, *, days: int = 7, limit: int = 10) -> list[ViewerRanking]:
        since = datetime.now(UTC) - timedelta(days=days)
        raw = await self._view_repo.top_viewer_user_ids(since=since, limit=limit)

        rankings: list[ViewerRanking] = []
        for user_id, count in raw:
            user = await self._user_repo.get_by_id(user_id)
            if user is not None:
                rankings.append(ViewerRanking(user=user, view_count=count))
        return rankings
