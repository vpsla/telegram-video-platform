"""
/attach_episode command handler.

Attaches an already-registered standalone Video to a Series as a
numbered episode, then notifies every follower of that series — this
closes the loop referenced by add_video.py's confirmation message and
implements the spec's "Nhận thông báo tập mới" requirement.
"""

from __future__ import annotations

import logging

from aiogram import Bot, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.favorite_repository import FavoriteRepository
from app.database.repositories.notification_repository import NotificationRepository
from app.database.repositories.series_repository import SeriesRepository
from app.database.repositories.user_repository import UserRepository
from app.database.repositories.video_repository import VideoRepository
from app.services.notification_service import NotificationService
from app.services.video_service import VideoService

logger = logging.getLogger(__name__)

router = Router(name="attach_episode")


@router.message(Command("attach_episode"))
async def attach_episode(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    bot: Bot,
) -> None:
    if not command.args:
        await message.answer(
            "Cách dùng: <code>/attach_episode &lt;video_id&gt; "
            "&lt;series_id&gt; &lt;số_tập&gt;</code>"
        )
        return

    parts = command.args.strip().split()
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        await message.answer(
            "⚠️ Cần đúng 3 số: video_id, series_id, số_tập.\n"
            "Ví dụ: <code>/attach_episode 12 3 5</code>"
        )
        return

    video_id, series_id, episode_number = (int(p) for p in parts)

    video_repo = VideoRepository(session)
    series_repo = SeriesRepository(session)
    video_service = VideoService(video_repo, series_repo)

    series = await series_repo.get_by_id(series_id)
    if series is None:
        await message.answer(f"⚠️ Không tìm thấy series ID {series_id}.")
        return

    try:
        await video_service.attach_to_series(
            video_id=video_id, series_id=series_id, episode_number=episode_number
        )
    except ValueError as exc:
        await message.answer(f"⚠️ {exc}")
        return

    await message.answer(
        f"✅ Đã gắn video {video_id} vào series <b>{series.title}</b> làm tập {episode_number}."
    )

    notification_service = NotificationService(
        NotificationRepository(session),
        FavoriteRepository(session),
        UserRepository(session),
    )
    sent_count = await notification_service.notify_new_episode(
        bot=bot,
        series_id=series_id,
        series_title=series.title,
        episode_number=episode_number,
    )
    if sent_count > 0:
        await message.answer(f"🔔 Đã gửi thông báo tập mới tới {sent_count} người theo dõi.")
