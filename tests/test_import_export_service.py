from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.category_repository import CategoryRepository
from app.database.repositories.series_repository import SeriesRepository
from app.services.import_export_service import ImportExportService
from app.services.series_service import SeriesService


def _build_service(db_session: AsyncSession) -> ImportExportService:
    series_repo = SeriesRepository(db_session)
    category_repo = CategoryRepository(db_session)
    series_service = SeriesService(series_repo, category_repo)
    return ImportExportService(series_repo, category_repo, series_service)


async def test_export_series_csv_contains_header_and_rows(db_session: AsyncSession) -> None:
    category_repo = CategoryRepository(db_session)
    series_repo = SeriesRepository(db_session)
    category = await category_repo.create(name="Tiên Hiệp", slug="tien-hiep")
    await series_repo.create(category_id=category.id, title="Test Series", slug="test-series")

    service = _build_service(db_session)
    csv_content = await service.export_series_csv()

    assert "title" in csv_content
    assert "Test Series" in csv_content
    assert "tien-hiep" in csv_content


async def test_export_series_csv_empty(db_session: AsyncSession) -> None:
    service = _build_service(db_session)
    csv_content = await service.export_series_csv()
    lines = csv_content.strip().split("\n")
    assert len(lines) == 1  # header only


async def test_import_series_csv_creates_rows(db_session: AsyncSession) -> None:
    category_repo = CategoryRepository(db_session)
    await category_repo.create(name="Đô Thị", slug="do-thi")

    service = _build_service(db_session)
    csv_content = (
        "title,category_slug,author\n" "Series A,do-thi,Author A\n" "Series B,do-thi,Author B\n"
    )
    result = await service.import_series_csv(csv_content)

    assert result.created == 2
    assert result.skipped == 0
    assert result.errors == []


async def test_import_series_csv_missing_columns(db_session: AsyncSession) -> None:
    service = _build_service(db_session)
    csv_content = "title\nOnly Title\n"
    result = await service.import_series_csv(csv_content)

    assert result.created == 0
    assert len(result.errors) == 1
    assert "missing required columns" in result.errors[0].message.lower()


async def test_import_series_csv_unknown_category_skipped(db_session: AsyncSession) -> None:
    service = _build_service(db_session)
    csv_content = "title,category_slug\nTitle A,khong-ton-tai\n"
    result = await service.import_series_csv(csv_content)

    assert result.created == 0
    assert result.skipped == 1
    assert "unknown category_slug" in result.errors[0].message.lower()


async def test_import_series_csv_missing_title_skipped(db_session: AsyncSession) -> None:
    category_repo = CategoryRepository(db_session)
    await category_repo.create(name="Cat", slug="cat")

    service = _build_service(db_session)
    csv_content = "title,category_slug\n,cat\n"
    result = await service.import_series_csv(csv_content)

    assert result.created == 0
    assert result.skipped == 1


async def test_import_series_csv_partial_failure_continues(db_session: AsyncSession) -> None:
    category_repo = CategoryRepository(db_session)
    await category_repo.create(name="Cat", slug="cat")

    service = _build_service(db_session)
    csv_content = (
        "title,category_slug\n"
        "Good Series,cat\n"
        "Bad Series,khong-ton-tai\n"
        "Another Good,cat\n"
    )
    result = await service.import_series_csv(csv_content)

    assert result.created == 2
    assert result.skipped == 1
    assert len(result.errors) == 1
