from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.category_repository import CategoryRepository
from app.database.repositories.series_repository import SeriesRepository
from app.database.repositories.user_repository import UserRepository
from app.database.repositories.video_repository import VideoRepository
from app.database.repositories.view_repository import ViewRepository
from app.services.statistics_service import StatisticsService


def _build_service(db_session: AsyncSession) -> StatisticsService:
    return StatisticsService(
        view_repo=ViewRepository(db_session),
        video_repo=VideoRepository(db_session),
        series_repo=SeriesRepository(db_session),
        user_repo=UserRepository(db_session),
    )


async def test_get_dashboard_stats(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    video_repo = VideoRepository(db_session)
    category_repo = CategoryRepository(db_session)
    series_repo = SeriesRepository(db_session)
    view_repo = ViewRepository(db_session)

    user, _ = await user_repo.get_or_create(telegram_id=1)
    category = await category_repo.create(name="Cat", slug="cat")
    await series_repo.create(category_id=category.id, title="S", slug="s")
    video = await video_repo.create(channel_id=-100, message_id=1, title="V")
    await view_repo.record(video_id=video.id, user_id=user.id)

    service = _build_service(db_session)
    stats = await service.get_dashboard_stats()

    assert stats.total_users == 1
    assert stats.total_series == 1
    assert stats.total_videos == 1
    assert stats.total_views == 1
    assert stats.views_7d == 1


async def test_get_dashboard_stats_empty(db_session: AsyncSession) -> None:
    service = _build_service(db_session)
    stats = await service.get_dashboard_stats()

    assert stats.total_users == 0
    assert stats.total_views == 0


async def test_get_top_videos_resolves_video_objects(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    video_repo = VideoRepository(db_session)
    view_repo = ViewRepository(db_session)

    user, _ = await user_repo.get_or_create(telegram_id=1)
    video = await video_repo.create(channel_id=-100, message_id=1, title="Popular")
    await view_repo.record(video_id=video.id, user_id=user.id)
    await view_repo.record(video_id=video.id, user_id=user.id)

    service = _build_service(db_session)
    rankings = await service.get_top_videos(days=7, limit=10)

    assert len(rankings) == 1
    assert rankings[0].video.title == "Popular"
    assert rankings[0].view_count == 2


async def test_get_top_videos_empty(db_session: AsyncSession) -> None:
    service = _build_service(db_session)
    rankings = await service.get_top_videos()
    assert rankings == []


async def test_get_top_series_prefers_featured(db_session: AsyncSession) -> None:
    category_repo = CategoryRepository(db_session)
    series_repo = SeriesRepository(db_session)
    category = await category_repo.create(name="Cat", slug="cat")

    featured = await series_repo.create(category_id=category.id, title="Featured", slug="f")
    await series_repo.update(featured.id, is_featured=True)
    await series_repo.increment_views(featured.id, delta=1)

    not_featured = await series_repo.create(category_id=category.id, title="Popular", slug="p")
    await series_repo.increment_views(not_featured.id, delta=100)

    service = _build_service(db_session)
    top = await service.get_top_series(limit=10)

    titles = [s.title for s in top]
    assert "Featured" in titles
    assert "Popular" in titles
    assert titles[0] == "Featured"  # featured surfaces first


async def test_get_top_series_empty(db_session: AsyncSession) -> None:
    service = _build_service(db_session)
    top = await service.get_top_series()
    assert top == []


async def test_get_top_viewers_resolves_user_objects(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    video_repo = VideoRepository(db_session)
    view_repo = ViewRepository(db_session)

    user, _ = await user_repo.get_or_create(telegram_id=1, username="alice")
    video = await video_repo.create(channel_id=-100, message_id=1, title="V")
    await view_repo.record(video_id=video.id, user_id=user.id)

    service = _build_service(db_session)
    rankings = await service.get_top_viewers(days=7, limit=10)

    assert len(rankings) == 1
    assert rankings[0].user.username == "alice"
    assert rankings[0].view_count == 1


async def test_get_views_per_day(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    video_repo = VideoRepository(db_session)
    view_repo = ViewRepository(db_session)

    user, _ = await user_repo.get_or_create(telegram_id=1)
    video = await video_repo.create(channel_id=-100, message_id=1, title="V")
    await view_repo.record(video_id=video.id, user_id=user.id)

    service = _build_service(db_session)
    daily = await service.get_views_per_day(days=7)

    assert len(daily) == 1
    assert daily[0].count == 1
