"""
Import/Export service.

CSV chosen per spec ("Import dữ liệu" / "Export dữ liệu") for
readability in Excel/Google Sheets, which is how admins are expected
to prepare bulk data. Export covers Series (the catalog-facing unit);
import creates Series rows from a CSV, validating each row
independently so one bad row doesn't abort the whole batch.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field

from app.database.repositories.category_repository import CategoryRepository
from app.database.repositories.series_repository import SeriesRepository
from app.services.series_service import SeriesService

_EXPORT_FIELDS = [
    "id",
    "title",
    "slug",
    "category_slug",
    "author",
    "description",
    "tags",
    "is_completed",
    "is_featured",
    "episode_count",
    "total_views",
]

_IMPORT_REQUIRED_FIELDS = {"title", "category_slug"}


@dataclass
class ImportRowError:
    row_number: int
    message: str


@dataclass
class ImportResult:
    created: int = 0
    skipped: int = 0
    errors: list[ImportRowError] = field(default_factory=list)


class ImportExportService:
    def __init__(
        self,
        series_repo: SeriesRepository,
        category_repo: CategoryRepository,
        series_service: SeriesService,
    ) -> None:
        self._series_repo = series_repo
        self._category_repo = category_repo
        self._series_service = series_service

    async def export_series_csv(self) -> str:
        """Return a CSV string of all series (used for admin export)."""
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=_EXPORT_FIELDS)
        writer.writeheader()

        # Fetch everything in pages to avoid loading an unbounded result
        # set into memory for very large catalogs.
        offset = 0
        page_size = 200
        while True:
            batch = await self._series_repo.list_newest(offset=offset, limit=page_size)
            if not batch:
                break
            for series in batch:
                category = await self._category_repo.get_by_id(series.category_id)
                writer.writerow(
                    {
                        "id": series.id,
                        "title": series.title,
                        "slug": series.slug,
                        "category_slug": category.slug if category else "",
                        "author": series.author or "",
                        "description": (series.description or "").replace("\n", " "),
                        "tags": series.tags or "",
                        "is_completed": series.is_completed,
                        "is_featured": series.is_featured,
                        "episode_count": series.episode_count,
                        "total_views": series.total_views,
                    }
                )
            offset += page_size

        return buffer.getvalue()

    async def import_series_csv(self, csv_content: str) -> ImportResult:
        """Bulk-create Series from a CSV. Required columns: title,
        category_slug. Optional: slug, author, description, tags.

        Each row is validated and committed independently at the
        service level (flush per row) so a single bad row is recorded
        as an error without aborting the rest of the batch.
        """
        result = ImportResult()
        reader = csv.DictReader(io.StringIO(csv_content))

        if reader.fieldnames is None or not _IMPORT_REQUIRED_FIELDS.issubset(
            {f.strip() for f in reader.fieldnames}
        ):
            result.errors.append(
                ImportRowError(
                    row_number=0,
                    message=f"CSV missing required columns: {sorted(_IMPORT_REQUIRED_FIELDS)}",
                )
            )
            return result

        for row_number, row in enumerate(reader, start=2):  # header is row 1
            title = (row.get("title") or "").strip()
            category_slug = (row.get("category_slug") or "").strip()

            if not title or not category_slug:
                result.skipped += 1
                result.errors.append(
                    ImportRowError(row_number=row_number, message="Missing title or category_slug")
                )
                continue

            category = await self._category_repo.get_by_slug(category_slug)
            if category is None:
                result.skipped += 1
                result.errors.append(
                    ImportRowError(
                        row_number=row_number,
                        message=f"Unknown category_slug: {category_slug!r}",
                    )
                )
                continue

            slug = (row.get("slug") or "").strip() or None
            try:
                await self._series_service.create_series(
                    category_id=category.id,
                    title=title,
                    slug=slug,
                    author=(row.get("author") or "").strip() or None,
                    description=(row.get("description") or "").strip() or None,
                    tags=(row.get("tags") or "").strip() or None,
                )
                result.created += 1
            except Exception as exc:
                result.skipped += 1
                result.errors.append(ImportRowError(row_number=row_number, message=str(exc)))

        return result
