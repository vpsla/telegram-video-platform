from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.category_repository import CategoryRepository
from app.database.repositories.series_repository import SeriesRepository
from app.database.repositories.video_repository import VideoRepository


async def _make_category(db_session: AsyncSession, slug: str = "tien-hiep") -> int:
    repo = CategoryRepository(db_session)
    category = await repo.create(name="Tiên Hiệp", slug=slug)
    return category.id


async def test_create_series_and_get_by_slug(db_session: AsyncSession) -> None:
    category_id = await _make_category(db_session)
    repo = SeriesRepository(db_session)

    series = await repo.create(
        category_id=category_id,
        title="Phàm Nhân Tu Tiên",
        slug="pham-nhan-tu-tien",
        author="Vong Ngữ",
    )

    fetched = await repo.get_by_slug("pham-nhan-tu-tien")
    assert fetched is not None
    assert fetched.id == series.id
    assert fetched.episode_count == 0
    assert fetched.total_views == 0


async def test_series_with_category_eager_load(db_session: AsyncSession) -> None:
    category_id = await _make_category(db_session)
    repo = SeriesRepository(db_session)
    series = await repo.create(category_id=category_id, title="Test", slug="test-series")

    fetched = await repo.get_by_id(series.id, with_category=True)
    assert fetched is not None
    assert fetched.category.slug == "tien-hiep"  # no lazy-load error


async def test_increment_counters(db_session: AsyncSession) -> None:
    category_id = await _make_category(db_session)
    repo = SeriesRepository(db_session)
    series = await repo.create(category_id=category_id, title="Test", slug="counters")

    await repo.increment_episode_count(series.id, delta=3)
    await repo.increment_views(series.id, delta=10)
    await repo.increment_followers(series.id, delta=1)

    reloaded = await repo.get_by_id(series.id)
    assert reloaded is not None
    assert reloaded.episode_count == 3
    assert reloaded.total_views == 10
    assert reloaded.follower_count == 1


async def test_list_newest_excludes_hidden(db_session: AsyncSession) -> None:
    category_id = await _make_category(db_session)
    repo = SeriesRepository(db_session)
    s1 = await repo.create(category_id=category_id, title="Visible", slug="visible")
    s2 = await repo.create(category_id=category_id, title="Hidden", slug="hidden")
    await repo.set_hidden(s2.id, hidden=True)

    newest = await repo.list_newest()
    slugs = [s.slug for s in newest]
    assert "visible" in slugs
    assert "hidden" not in slugs
    assert s1.slug == "visible"


async def test_list_featured(db_session: AsyncSession) -> None:
    category_id = await _make_category(db_session)
    repo = SeriesRepository(db_session)
    s1 = await repo.create(category_id=category_id, title="Featured", slug="featured-1")
    await repo.update(s1.id, is_featured=True)
    await repo.create(category_id=category_id, title="Not featured", slug="not-featured")

    featured = await repo.list_featured()
    assert len(featured) == 1
    assert featured[0].slug == "featured-1"


async def test_search_by_title_author_tags(db_session: AsyncSession) -> None:
    category_id = await _make_category(db_session)
    repo = SeriesRepository(db_session)
    await repo.create(
        category_id=category_id,
        title="Đấu Phá Thương Khung",
        slug="dou-po",
        author="Thiên Tàm Thổ Đậu",
        tags="huyen-huyen,dau-khi",
    )

    by_title = await repo.search("Đấu Phá")
    assert len(by_title) == 1

    by_author = await repo.search("Thiên Tàm")
    assert len(by_author) == 1

    by_tag = await repo.search("dau-khi")
    assert len(by_tag) == 1

    no_match = await repo.search("khong-ton-tai")
    assert no_match == []


async def test_series_count_total(db_session: AsyncSession) -> None:
    category_id = await _make_category(db_session)
    repo = SeriesRepository(db_session)
    await repo.create(category_id=category_id, title="A", slug="a")
    await repo.create(category_id=category_id, title="B", slug="b")

    assert await repo.count_total() == 2


# --- VideoRepository ---------------------------------------------------------


async def test_create_video_and_get_by_channel_message(db_session: AsyncSession) -> None:
    repo = VideoRepository(db_session)
    video = await repo.create(channel_id=-1001234567890, message_id=42, title="Chương 1")

    fetched = await repo.get_by_channel_message(-1001234567890, 42)
    assert fetched is not None
    assert fetched.id == video.id


async def test_video_view_count_increment(db_session: AsyncSession) -> None:
    repo = VideoRepository(db_session)
    video = await repo.create(channel_id=-100111, message_id=1, title="Test")

    await repo.increment_view_count(video.id)
    await repo.increment_view_count(video.id)

    reloaded = await repo.get_by_id(video.id)
    assert reloaded is not None
    assert reloaded.view_count == 2


async def test_attach_as_episode_and_list_for_series(db_session: AsyncSession) -> None:
    category_id = await _make_category(db_session)
    series_repo = SeriesRepository(db_session)
    video_repo = VideoRepository(db_session)

    series = await series_repo.create(category_id=category_id, title="S", slug="s")
    v1 = await video_repo.create(channel_id=-100, message_id=1, title="Ep1")
    v2 = await video_repo.create(channel_id=-100, message_id=2, title="Ep2")

    await video_repo.attach_as_episode(video_id=v1.id, series_id=series.id, episode_number=1)
    await video_repo.attach_as_episode(video_id=v2.id, series_id=series.id, episode_number=2)

    episodes = await video_repo.list_episodes_for_series(series.id)
    assert [e.episode_number for e in episodes] == [1, 2]
    assert episodes[0].video.title == "Ep1"  # eager-loaded, no lazy error


async def test_get_episode_by_series_and_number(db_session: AsyncSession) -> None:
    category_id = await _make_category(db_session)
    series_repo = SeriesRepository(db_session)
    video_repo = VideoRepository(db_session)

    series = await series_repo.create(category_id=category_id, title="S", slug="s2")
    v1 = await video_repo.create(channel_id=-100, message_id=1, title="Ep1")
    await video_repo.attach_as_episode(video_id=v1.id, series_id=series.id, episode_number=1)

    found = await video_repo.get_episode_by_series_and_number(series.id, 1)
    assert found is not None
    assert found.video_id == v1.id

    not_found = await video_repo.get_episode_by_series_and_number(series.id, 999)
    assert not_found is None


async def test_list_newest_standalone_excludes_episodes(db_session: AsyncSession) -> None:
    category_id = await _make_category(db_session)
    series_repo = SeriesRepository(db_session)
    video_repo = VideoRepository(db_session)

    series = await series_repo.create(category_id=category_id, title="S", slug="s3")
    standalone = await video_repo.create(channel_id=-100, message_id=10, title="Standalone")
    episode_video = await video_repo.create(channel_id=-100, message_id=11, title="EpVideo")
    await video_repo.attach_as_episode(
        video_id=episode_video.id, series_id=series.id, episode_number=1
    )

    standalones = await video_repo.list_newest_standalone()
    ids = [v.id for v in standalones]
    assert standalone.id in ids
    assert episode_video.id not in ids


async def test_video_count_total(db_session: AsyncSession) -> None:
    repo = VideoRepository(db_session)
    await repo.create(channel_id=-100, message_id=1, title="A")
    await repo.create(channel_id=-100, message_id=2, title="B")

    assert await repo.count_total() == 2
