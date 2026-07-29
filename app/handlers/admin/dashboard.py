"""
Full admin dashboard (Phase 6).

Extends the Phase 5 headline-counter dashboard with top video, top
series, top viewer, and a daily view-count breakdown, all backed by
StatisticsService.
"""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.series_repository import SeriesRepository
from app.database.repositories.user_repository import UserRepository
from app.database.repositories.video_repository import VideoRepository
from app.database.repositories.view_repository import ViewRepository
from app.services.statistics_service import StatisticsService

logger = logging.getLogger(__name__)

router = Router(name="admin_dashboard")


def _build_service(session: AsyncSession) -> StatisticsService:
    return StatisticsService(
        view_repo=ViewRepository(session),
        video_repo=VideoRepository(session),
        series_repo=SeriesRepository(session),
        user_repo=UserRepository(session),
    )


@router.message(Command("dashboard"))
async def show_dashboard(message: Message, session: AsyncSession) -> None:
    service = _build_service(session)
    stats = await service.get_dashboard_stats()

    await message.answer(
        "📊 <b>Dashboard tổng quan</b>\n\n"
        f"👥 Tổng số user: <b>{stats.total_users}</b>\n"
        f"🆕 User mới (7 ngày): <b>{stats.new_users_7d}</b>\n"
        f"📚 Tổng số series: <b>{stats.total_series}</b>\n"
        f"🎬 Tổng số video: <b>{stats.total_videos}</b>\n"
        f"👁️ Tổng lượt xem: <b>{stats.total_views}</b>\n"
        f"👁️ Lượt xem (7 ngày): <b>{stats.views_7d}</b>\n\n"
        "Dùng /top_videos, /top_series, /top_viewers, /views_chart "
        "để xem thống kê chi tiết."
    )


@router.message(Command("top_videos"))
async def show_top_videos(message: Message, session: AsyncSession) -> None:
    service = _build_service(session)
    rankings = await service.get_top_videos(days=7, limit=10)

    if not rankings:
        await message.answer("Chưa có dữ liệu lượt xem trong 7 ngày qua.")
        return

    lines = ["🏆 <b>Top 10 video (7 ngày qua):</b>\n"]
    for i, ranking in enumerate(rankings, start=1):
        lines.append(f"{i}. {ranking.video.title} — {ranking.view_count} lượt xem")
    await message.answer("\n".join(lines))


@router.message(Command("top_series"))
async def show_top_series(message: Message, session: AsyncSession) -> None:
    service = _build_service(session)
    series_list = await service.get_top_series(limit=10)

    if not series_list:
        await message.answer("Chưa có series nào.")
        return

    lines = ["🏆 <b>Top 10 series:</b>\n"]
    for i, series in enumerate(series_list, start=1):
        lines.append(f"{i}. {series.title} — {series.total_views} lượt xem")
    await message.answer("\n".join(lines))


@router.message(Command("top_viewers"))
async def show_top_viewers(message: Message, session: AsyncSession) -> None:
    service = _build_service(session)
    rankings = await service.get_top_viewers(days=7, limit=10)

    if not rankings:
        await message.answer("Chưa có dữ liệu người xem trong 7 ngày qua.")
        return

    lines = ["🏆 <b>Top 10 người xem (7 ngày qua):</b>\n"]
    for i, ranking in enumerate(rankings, start=1):
        lines.append(f"{i}. {ranking.user.display_name} — {ranking.view_count} lượt xem")
    await message.answer("\n".join(lines))


@router.message(Command("views_chart"))
async def show_views_chart(message: Message, session: AsyncSession) -> None:
    service = _build_service(session)
    daily = await service.get_views_per_day(days=7)

    if not daily:
        await message.answer("Chưa có dữ liệu lượt xem trong 7 ngày qua.")
        return

    lines = ["📈 <b>Lượt xem theo ngày (7 ngày qua):</b>\n"]
    for entry in daily:
        lines.append(f"{entry.day}: {entry.count} lượt xem")
    await message.answer("\n".join(lines))
