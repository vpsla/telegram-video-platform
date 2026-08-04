"""REST API endpoints for the Telegram Mini App."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.category_repository import CategoryRepository
from app.database.repositories.history_repository import HistoryRepository
from app.database.repositories.series_repository import SeriesRepository
from app.database.repositories.user_repository import UserRepository
from app.database.repositories.video_repository import VideoRepository
from app.database.repositories.watch_progress_repository import WatchProgressRepository

logger = logging.getLogger(__name__)

api_router = APIRouter(prefix="/api/v1", tags=["miniapp"])


def _validate_init_data(init_data: str, bot_token: str) -> dict:
    try:
        parsed = dict(item.split("=", 1) for item in init_data.split("&"))
        received_hash = parsed.pop("hash", "")
        data_check = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        computed = hmac.new(secret_key, data_check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(computed, received_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid initData")
        return json.loads(unquote(parsed.get("user", "{}")))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid initData"
        ) from exc


async def get_db_session():
    from app.main import session_factory

    async with session_factory() as session:
        yield session


async def get_current_user(
    request: Request,
    init_data: str = Query(...),
    session: AsyncSession = Depends(get_db_session),
):
    from app.config.settings import get_settings

    settings = get_settings()
    tg_user = _validate_init_data(init_data, settings.telegram.bot_token.get_secret_value())
    telegram_id = tg_user.get("id")
    if not telegram_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No user id")
    user_repo = UserRepository(session)
    user, _ = await user_repo.get_or_create(
        telegram_id=telegram_id,
        username=tg_user.get("username"),
        first_name=tg_user.get("first_name"),
        last_name=tg_user.get("last_name"),
    )
    return user


def _serialize_series(s) -> dict:
    return {
        "id": s.id,
        "title": s.title,
        "slug": s.slug,
        "author": s.author,
        "description": s.description,
        "thumbnail_file_id": s.thumbnail_file_id,
        "episode_count": s.episode_count,
        "total_views": s.total_views,
        "is_completed": s.is_completed,
        "is_featured": s.is_featured,
        "tags": s.tags,
    }


@api_router.get("/series/newest")
async def get_newest_series(
    offset: int = 0,
    limit: int = 20,
    session: AsyncSession = Depends(get_db_session),
):
    repo = SeriesRepository(session)
    items = await repo.list_newest(offset=offset, limit=min(limit, 50))
    return {
        "items": [_serialize_series(s) for s in items],
        "offset": offset,
        "has_more": len(items) == limit,
    }


@api_router.get("/series/featured")
async def get_featured_series(
    offset: int = 0,
    limit: int = 20,
    session: AsyncSession = Depends(get_db_session),
):
    repo = SeriesRepository(session)
    items = await repo.list_featured(offset=offset, limit=min(limit, 50))
    return {
        "items": [_serialize_series(s) for s in items],
        "offset": offset,
        "has_more": len(items) == limit,
    }


@api_router.get("/series/search")
async def search_series(
    q: str = Query(..., min_length=1),
    offset: int = 0,
    limit: int = 20,
    session: AsyncSession = Depends(get_db_session),
):
    repo = SeriesRepository(session)
    items = await repo.search(q.strip(), offset=offset, limit=min(limit, 50))
    return {
        "query": q,
        "items": [_serialize_series(s) for s in items],
        "has_more": len(items) == limit,
    }


@api_router.get("/series/{series_id}")
async def get_series_detail(
    series_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    series_repo = SeriesRepository(session)
    video_repo = VideoRepository(session)
    series = await series_repo.get_by_id(series_id, with_category=True)
    if series is None or series.is_hidden:
        raise HTTPException(status_code=404, detail="Series not found")
    episodes = await video_repo.list_episodes_for_series(series_id)
    return {
        **_serialize_series(series),
        "category_name": series.category.name if series.category else None,
        "episodes": [
            {
                "episode_number": ep.episode_number,
                "title": ep.title_override or f"Tập {ep.episode_number}",
                "video_id": ep.video_id,
                "duration_seconds": ep.video.duration_seconds,
            }
            for ep in episodes
        ],
    }


@api_router.get("/categories")
async def get_categories(session: AsyncSession = Depends(get_db_session)):
    repo = CategoryRepository(session)
    cats = await repo.list_active()
    return {
        "items": [
            {"id": c.id, "name": c.name, "slug": c.slug, "icon_emoji": c.icon_emoji} for c in cats
        ]
    }


@api_router.get("/categories/{category_id}/series")
async def get_series_by_category(
    category_id: int,
    offset: int = 0,
    limit: int = 20,
    session: AsyncSession = Depends(get_db_session),
):
    repo = SeriesRepository(session)
    items = await repo.list_by_category(category_id, offset=offset, limit=min(limit, 50))
    return {
        "items": [_serialize_series(s) for s in items],
        "offset": offset,
        "has_more": len(items) == limit,
    }


@api_router.get("/history")
async def get_history(
    offset: int = 0,
    limit: int = 20,
    session: AsyncSession = Depends(get_db_session),
    user=Depends(get_current_user),
):
    repo = HistoryRepository(session)
    entries = await repo.list_for_user(user.id, offset=offset, limit=min(limit, 50))
    return {
        "items": [
            {
                "id": e.id,
                "video_id": e.video_id,
                "video_title": e.video.title,
                "watched_at": e.created_at.isoformat(),
            }
            for e in entries
        ],
        "offset": offset,
        "has_more": len(entries) == limit,
    }


@api_router.get("/continue-watching")
async def get_continue_watching(
    session: AsyncSession = Depends(get_db_session),
    user=Depends(get_current_user),
):
    repo = WatchProgressRepository(session)
    entries = await repo.list_continue_watching(user.id, limit=10)
    return {
        "items": [
            {
                "video_id": e.video_id,
                "video_title": e.video.title,
                "position_seconds": e.position_seconds,
            }
            for e in entries
        ]
    }


@api_router.get("/me")
async def get_me(user=Depends(get_current_user)):
    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "display_name": user.display_name,
        "is_vip": user.is_currently_vip,
        "total_watch_seconds": user.total_watch_seconds,
        "joined_at": user.created_at.isoformat(),
    }
