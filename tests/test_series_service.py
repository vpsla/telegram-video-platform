from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.category_repository import CategoryRepository
from app.database.repositories.series_repository import SeriesRepository
from app.services.series_service import (
    CategoryNotFoundError,
    DuplicateSlugError,
    SeriesService,
    slugify,
)


def test_slugify_basic() -> None:
    assert slugify("Phàm Nhân Tu Tiên") != ""
    assert slugify("Hello World") == "hello-world"
    assert slugify("") == "item"


async def test_create_series_success(db_session: AsyncSession) -> None:
    category_repo = CategoryRepository(db_session)
    series_repo = SeriesRepository(db_session)
    service = SeriesService(series_repo, category_repo)

    category = await category_repo.create(name="Tiên Hiệp", slug="tien-hiep")
    series = await service.create_series(category_id=category.id, title="Test Series")

    assert series.category_id == category.id
    assert series.slug  # auto-generated


async def test_create_series_unknown_category_raises(db_session: AsyncSession) -> None:
    category_repo = CategoryRepository(db_session)
    series_repo = SeriesRepository(db_session)
    service = SeriesService(series_repo, category_repo)

    with pytest.raises(CategoryNotFoundError):
        await service.create_series(category_id=99999, title="X")


async def test_create_series_duplicate_slug_raises(db_session: AsyncSession) -> None:
    category_repo = CategoryRepository(db_session)
    series_repo = SeriesRepository(db_session)
    service = SeriesService(series_repo, category_repo)

    category = await category_repo.create(name="Cat", slug="cat")
    await service.create_series(category_id=category.id, title="A", slug="fixed-slug")

    with pytest.raises(DuplicateSlugError):
        await service.create_series(category_id=category.id, title="B", slug="fixed-slug")


async def test_toggle_featured_and_completed(db_session: AsyncSession) -> None:
    category_repo = CategoryRepository(db_session)
    series_repo = SeriesRepository(db_session)
    service = SeriesService(series_repo, category_repo)

    category = await category_repo.create(name="Cat", slug="cat2")
    series = await service.create_series(category_id=category.id, title="A")

    updated = await service.toggle_featured(series.id, featured=True)
    assert updated.is_featured is True

    updated = await service.toggle_completed(series.id, completed=True)
    assert updated.is_completed is True
