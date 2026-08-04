from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.category_repository import CategoryRepository
from app.database.repositories.favorite_repository import FavoriteRepository
from app.database.repositories.history_repository import HistoryRepository
from app.database.repositories.series_repository import SeriesRepository
from app.database.repositories.user_repository import UserRepository
from app.database.repositories.video_repository import VideoRepository
from app.database.repositories.watch_progress_repository import WatchProgressRepository
from app.services.favorite_service import FavoriteService, SeriesNotFoundError
from app.services.history_service import HistoryService
from app.services.search_service import CategoryNotFoundError, SearchService

# --- SearchService -------------------------------------------------------------


async def test_search_by_keyword(db_session: AsyncSession) -> None:
    category_repo = CategoryRepository(db_session)
    series_repo = SeriesRepository(db_session)
    service = SearchService(series_repo, category_repo)

    category = await category_repo.create(name="Tiên Hiệp", slug="tien-hiep")
    await series_repo.create(
        category_id=category.id, title="Phàm Nhân Tu Tiên", slug="pham-nhan", author="Vong Ngữ"
    )

    results = await service.search_by_keyword("Phàm Nhân")
    assert len(results) == 1

    empty = await service.search_by_keyword("   ")
    assert empty == []


async def test_search_by_category_slug(db_session: AsyncSession) -> None:
    category_repo = CategoryRepository(db_session)
    series_repo = SeriesRepository(db_session)
    service = SearchService(series_repo, category_repo)

    category = await category_repo.create(name="Đô Thị", slug="do-thi")
    await series_repo.create(category_id=category.id, title="S1", slug="s1")

    results = await service.search_by_category_slug("do-thi")
    assert len(results) == 1

    with pytest.raises(CategoryNotFoundError):
        await service.search_by_category_slug("khong-ton-tai")


async def test_get_series_by_slug(db_session: AsyncSession) -> None:
    category_repo = CategoryRepository(db_session)
    series_repo = SeriesRepository(db_session)
    service = SearchService(series_repo, category_repo)

    category = await category_repo.create(name="Cat", slug="cat")
    await series_repo.create(category_id=category.id, title="Title", slug="my-slug")

    found = await service.get_series_by_slug("my-slug")
    assert found is not None
    assert found.title == "Title"
    assert await service.get_series_by_slug("no-such-slug") is None


# --- HistoryService --------------------------------------------------------------


async def test_history_service_record_and_progress(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    video_repo = VideoRepository(db_session)
    history_repo = HistoryRepository(db_session)
    progress_repo = WatchProgressRepository(db_session)
    service = HistoryService(history_repo, progress_repo)

    user, _ = await user_repo.get_or_create(telegram_id=1)
    video = await video_repo.create(channel_id=-100, message_id=1, title="V1")

    await service.record_watch_start(user_id=user.id, video_id=video.id)
    await service.update_progress(user_id=user.id, video_id=video.id, position_seconds=42)

    history = await service.get_history(user.id)
    assert len(history) == 1

    continuing = await service.get_continue_watching(user.id)
    assert len(continuing) == 1
    assert continuing[0].position_seconds == 42


async def test_history_service_clear(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    video_repo = VideoRepository(db_session)
    history_repo = HistoryRepository(db_session)
    progress_repo = WatchProgressRepository(db_session)
    service = HistoryService(history_repo, progress_repo)

    user, _ = await user_repo.get_or_create(telegram_id=2)
    video = await video_repo.create(channel_id=-100, message_id=2, title="V2")
    await service.record_watch_start(user_id=user.id, video_id=video.id)

    cleared = await service.clear_history(user.id)
    assert cleared == 1
    assert await service.get_history(user.id) == []


async def test_history_service_continue_watching_videos(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    video_repo = VideoRepository(db_session)
    history_repo = HistoryRepository(db_session)
    progress_repo = WatchProgressRepository(db_session)
    service = HistoryService(history_repo, progress_repo)

    user, _ = await user_repo.get_or_create(telegram_id=3)
    video = await video_repo.create(channel_id=-100, message_id=3, title="V3")
    await service.update_progress(user_id=user.id, video_id=video.id, position_seconds=10)

    videos = await service.get_continue_watching_videos(user.id)
    assert len(videos) == 1
    assert videos[0].title == "V3"


# --- FavoriteService ------------------------------------------------------------


async def test_favorite_service_follow_increments_counter(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    category_repo = CategoryRepository(db_session)
    series_repo = SeriesRepository(db_session)
    favorite_repo = FavoriteRepository(db_session)
    service = FavoriteService(favorite_repo, series_repo)

    user, _ = await user_repo.get_or_create(telegram_id=1)
    category = await category_repo.create(name="Cat", slug="cat")
    series = await series_repo.create(category_id=category.id, title="S", slug="s")

    await service.follow(user_id=user.id, series_id=series.id)

    reloaded = await series_repo.get_by_id(series.id)
    assert reloaded is not None
    assert reloaded.follower_count == 1
    assert await service.is_following(user.id, series.id) is True


async def test_favorite_service_follow_unknown_series_raises(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    series_repo = SeriesRepository(db_session)
    favorite_repo = FavoriteRepository(db_session)
    service = FavoriteService(favorite_repo, series_repo)

    user, _ = await user_repo.get_or_create(telegram_id=2)
    with pytest.raises(SeriesNotFoundError):
        await service.follow(user_id=user.id, series_id=99999)


async def test_favorite_service_unfollow_decrements_counter(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    category_repo = CategoryRepository(db_session)
    series_repo = SeriesRepository(db_session)
    favorite_repo = FavoriteRepository(db_session)
    service = FavoriteService(favorite_repo, series_repo)

    user, _ = await user_repo.get_or_create(telegram_id=3)
    category = await category_repo.create(name="Cat", slug="cat2")
    series = await series_repo.create(category_id=category.id, title="S", slug="s2")

    await service.follow(user_id=user.id, series_id=series.id)
    removed = await service.unfollow(user_id=user.id, series_id=series.id)
    assert removed is True

    reloaded = await series_repo.get_by_id(series.id)
    assert reloaded is not None
    assert reloaded.follower_count == 0


async def test_favorite_service_toggle(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    category_repo = CategoryRepository(db_session)
    series_repo = SeriesRepository(db_session)
    favorite_repo = FavoriteRepository(db_session)
    service = FavoriteService(favorite_repo, series_repo)

    user, _ = await user_repo.get_or_create(telegram_id=4)
    category = await category_repo.create(name="Cat", slug="cat3")
    series = await series_repo.create(category_id=category.id, title="S", slug="s3")

    now_following = await service.toggle(user_id=user.id, series_id=series.id)
    assert now_following is True

    now_following_again = await service.toggle(user_id=user.id, series_id=series.id)
    assert now_following_again is False
