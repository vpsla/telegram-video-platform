from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.history_repository import HistoryRepository
from app.database.repositories.user_repository import UserRepository
from app.database.repositories.video_repository import VideoRepository
from app.database.repositories.watch_progress_repository import WatchProgressRepository


async def _setup_user_and_videos(db_session: AsyncSession, n: int = 2):
    user_repo = UserRepository(db_session)
    video_repo = VideoRepository(db_session)
    user, _ = await user_repo.get_or_create(telegram_id=1)
    videos = [
        await video_repo.create(channel_id=-100, message_id=i, title=f"V{i}")
        for i in range(1, n + 1)
    ]
    return user, videos


# --- HistoryRepository -------------------------------------------------------


async def test_record_and_list_for_user(db_session: AsyncSession) -> None:
    user, videos = await _setup_user_and_videos(db_session)
    repo = HistoryRepository(db_session)

    await repo.record(user_id=user.id, video_id=videos[0].id)
    await repo.record(user_id=user.id, video_id=videos[1].id)

    history = await repo.list_for_user(user.id)
    assert len(history) == 2
    assert history[0].video.title == "V2"  # most recent first


async def test_count_for_user(db_session: AsyncSession) -> None:
    user, videos = await _setup_user_and_videos(db_session, n=1)
    repo = HistoryRepository(db_session)
    await repo.record(user_id=user.id, video_id=videos[0].id)
    await repo.record(user_id=user.id, video_id=videos[0].id)

    assert await repo.count_for_user(user.id) == 2


async def test_clear_for_user(db_session: AsyncSession) -> None:
    user, videos = await _setup_user_and_videos(db_session, n=1)
    repo = HistoryRepository(db_session)
    await repo.record(user_id=user.id, video_id=videos[0].id)

    cleared = await repo.clear_for_user(user.id)
    assert cleared == 1
    assert await repo.count_for_user(user.id) == 0


async def test_list_recently_watched_videos_deduplicates(db_session: AsyncSession) -> None:
    user, videos = await _setup_user_and_videos(db_session, n=2)
    repo = HistoryRepository(db_session)

    await repo.record(user_id=user.id, video_id=videos[0].id)
    await repo.record(user_id=user.id, video_id=videos[1].id)
    await repo.record(user_id=user.id, video_id=videos[0].id)  # watched again

    recent = await repo.list_recently_watched_videos(user.id)
    assert [v.id for v in recent] == [videos[0].id, videos[1].id]


# --- WatchProgressRepository ---------------------------------------------------


async def test_upsert_creates_then_updates(db_session: AsyncSession) -> None:
    user, videos = await _setup_user_and_videos(db_session, n=1)
    repo = WatchProgressRepository(db_session)

    first = await repo.upsert(user_id=user.id, video_id=videos[0].id, position_seconds=30)
    assert first.position_seconds == 30

    second = await repo.upsert(user_id=user.id, video_id=videos[0].id, position_seconds=90)
    assert second.id == first.id
    assert second.position_seconds == 90


async def test_list_continue_watching_excludes_completed(db_session: AsyncSession) -> None:
    user, videos = await _setup_user_and_videos(db_session, n=2)
    repo = WatchProgressRepository(db_session)

    await repo.upsert(user_id=user.id, video_id=videos[0].id, position_seconds=10)
    await repo.upsert(
        user_id=user.id, video_id=videos[1].id, position_seconds=100, is_completed=True
    )

    continuing = await repo.list_continue_watching(user.id)
    assert len(continuing) == 1
    assert continuing[0].video_id == videos[0].id
    assert continuing[0].video.title == "V1"  # eager-loaded


async def test_delete_progress(db_session: AsyncSession) -> None:
    user, videos = await _setup_user_and_videos(db_session, n=1)
    repo = WatchProgressRepository(db_session)
    await repo.upsert(user_id=user.id, video_id=videos[0].id, position_seconds=5)

    assert await repo.delete(user.id, videos[0].id) is True
    assert await repo.get(user.id, videos[0].id) is None
    assert await repo.delete(user.id, videos[0].id) is False
