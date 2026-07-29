"""Series service — business logic on top of SeriesRepository."""

from __future__ import annotations

import re

from app.database.models.series import Series
from app.database.repositories.category_repository import CategoryRepository
from app.database.repositories.series_repository import SeriesRepository


class CategoryNotFoundError(Exception):
    pass


class DuplicateSlugError(Exception):
    pass


def slugify(text: str) -> str:
    """Very small ASCII slugifier. Vietnamese diacritics are stripped by
    the caller-provided slug when needed; this is a safe fallback for
    auto-generating one from a title."""
    normalized = re.sub(r"[^a-zA-Z0-9\s-]", "", text).strip().lower()
    return re.sub(r"[\s-]+", "-", normalized) or "item"


class SeriesService:
    def __init__(self, series_repo: SeriesRepository, category_repo: CategoryRepository) -> None:
        self._series_repo = series_repo
        self._category_repo = category_repo

    async def create_series(
        self,
        *,
        category_id: int,
        title: str,
        slug: str | None = None,
        description: str | None = None,
        author: str | None = None,
        thumbnail_file_id: str | None = None,
        tags: str | None = None,
    ) -> Series:
        category = await self._category_repo.get_by_id(category_id)
        if category is None:
            raise CategoryNotFoundError(f"Category {category_id} not found")

        final_slug = slug or slugify(title)
        if await self._series_repo.get_by_slug(final_slug) is not None:
            raise DuplicateSlugError(f"Slug {final_slug!r} already in use")

        return await self._series_repo.create(
            category_id=category_id,
            title=title,
            slug=final_slug,
            description=description,
            author=author,
            thumbnail_file_id=thumbnail_file_id,
            tags=tags,
        )

    async def toggle_featured(self, series_id: int, *, featured: bool) -> Series:
        return await self._series_repo.update(series_id, is_featured=featured)

    async def toggle_completed(self, series_id: int, *, completed: bool) -> Series:
        return await self._series_repo.update(series_id, is_completed=completed)
