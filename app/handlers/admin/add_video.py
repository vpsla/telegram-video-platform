"""
Add-video admin flow.

Sequence (per spec: bot only stores channel_id/message_id/title/etc.,
never re-uploads):
  1. Admin forwards a message FROM the storage channel to the bot.
  2. Bot extracts channel_id + message_id from the forwarded message.
  3. Admin provides title, optional description, category.
  4. Admin chooses: attach to an existing series as an episode, or
     leave as a standalone video.
"""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.category_repository import CategoryRepository
from app.database.repositories.series_repository import SeriesRepository
from app.database.repositories.video_repository import VideoRepository
from app.keyboards.admin import category_choice_keyboard
from app.services.video_service import VideoService
from app.states.add_video import AddVideoStates

logger = logging.getLogger(__name__)

router = Router(name="add_video")


@router.message(Command("add_video"))
async def start_add_video(message: Message, state: FSMContext) -> None:
    await state.set_state(AddVideoStates.waiting_for_forward)
    await message.answer(
        "📥 Hãy <b>forward</b> tin nhắn video từ Channel lưu trữ đến đây.\n\n"
        "Bot sẽ không tải lại video — chỉ lưu vị trí (channel_id, message_id)."
    )


@router.message(AddVideoStates.waiting_for_forward)
async def receive_forwarded_video(message: Message, state: FSMContext, settings) -> None:
    if message.forward_from_chat is None:
        await message.answer(
            "⚠️ Vui lòng forward tin nhắn <b>từ Channel lưu trữ</b>, không phải gửi trực tiếp."
        )
        return

    forwarded_channel_id = message.forward_from_chat.id
    forwarded_message_id = message.forward_from_message_id

    if forwarded_channel_id != settings.telegram.storage_channel_id:
        await message.answer(
            "⚠️ Tin nhắn này không phải từ Channel lưu trữ đã cấu hình. Vui lòng thử lại."
        )
        return

    if forwarded_message_id is None:
        await message.answer("⚠️ Không xác định được message_id gốc. Vui lòng thử lại.")
        return

    await state.update_data(channel_id=forwarded_channel_id, message_id=forwarded_message_id)
    await state.set_state(AddVideoStates.waiting_for_title)
    await message.answer("✏️ Nhập <b>tiêu đề</b> cho video:")


@router.message(AddVideoStates.waiting_for_title)
async def receive_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if not title:
        await message.answer("⚠️ Tiêu đề không được để trống. Vui lòng nhập lại:")
        return

    await state.update_data(title=title)
    await state.set_state(AddVideoStates.waiting_for_description)
    await message.answer("📝 Nhập <b>mô tả</b> (hoặc gửi /skip để bỏ qua):")


@router.message(Command("skip"), AddVideoStates.waiting_for_description)
async def skip_description(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.update_data(description=None)
    await _ask_for_category(message, state, session)


@router.message(AddVideoStates.waiting_for_description)
async def receive_description(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.update_data(description=(message.text or "").strip() or None)
    await _ask_for_category(message, state, session)


async def _ask_for_category(message: Message, state: FSMContext, session: AsyncSession) -> None:
    category_repo = CategoryRepository(session)
    categories = await category_repo.list_active()
    if not categories:
        await message.answer(
            "⚠️ Chưa có thể loại nào. Hãy tạo thể loại trước bằng /admin → Quản lý thể loại."
        )
        await state.clear()
        return

    await state.set_state(AddVideoStates.waiting_for_category)
    await message.answer(
        "🏷️ Chọn thể loại cho video:",
        reply_markup=category_choice_keyboard(categories, callback_prefix="add_video:category"),
    )


@router.callback_query(
    AddVideoStates.waiting_for_category, F.data.startswith("add_video:category:")
)
async def receive_category_and_save(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if callback.data is None:
        return
    category_id = int(callback.data.split(":")[-1])
    data = await state.get_data()

    video_service = VideoService(VideoRepository(session), SeriesRepository(session))
    video = await video_service.register_video(
        channel_id=data["channel_id"],
        message_id=data["message_id"],
        title=data["title"],
        description=data.get("description"),
        category_id=category_id,
    )

    await state.clear()
    if callback.message is not None:
        await callback.message.edit_text(
            f"✅ Đã thêm video <b>{video.title}</b> (ID: {video.id}).\n\n"
            "Dùng /attach_episode để gắn video này vào một series, nếu cần."
        )
    await callback.answer()
