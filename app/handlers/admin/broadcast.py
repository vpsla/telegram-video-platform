"""Broadcast admin flow: compose -> confirm -> send to all users."""

from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.user_repository import UserRepository
from app.keyboards.admin import confirm_cancel_keyboard
from app.services.broadcast_service import BroadcastService
from app.states.broadcast import BroadcastStates

logger = logging.getLogger(__name__)

router = Router(name="broadcast")


@router.message(Command("broadcast"))
async def start_broadcast(message: Message, state: FSMContext) -> None:
    await state.set_state(BroadcastStates.waiting_for_content)
    await message.answer("📢 Nhập nội dung bạn muốn <b>broadcast</b> tới toàn bộ user:")


@router.message(BroadcastStates.waiting_for_content)
async def receive_broadcast_content(message: Message, state: FSMContext) -> None:
    content = (message.text or "").strip()
    if not content:
        await message.answer("⚠️ Nội dung không được để trống. Vui lòng nhập lại:")
        return

    await state.update_data(content=content)
    await state.set_state(BroadcastStates.waiting_for_confirmation)
    await message.answer(
        f"📋 <b>Xem trước nội dung:</b>\n\n{content}\n\n"
        "Bạn có chắc chắn muốn gửi tới toàn bộ user không?",
        reply_markup=confirm_cancel_keyboard(confirm_data="broadcast:confirm"),
    )


@router.callback_query(BroadcastStates.waiting_for_confirmation, F.data == "broadcast:confirm")
async def confirm_broadcast(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
) -> None:
    data = await state.get_data()
    content = data.get("content", "")
    await state.clear()

    if callback.message is not None:
        await callback.message.edit_text("⏳ Đang gửi broadcast, vui lòng chờ...")
    await callback.answer()

    service = BroadcastService(UserRepository(session))
    result = await service.broadcast_text(bot=bot, text=content)

    if callback.message is not None:
        await callback.message.answer(
            "✅ <b>Broadcast hoàn tất.</b>\n\n"
            f"Tổng số user: {result.total}\n"
            f"Đã gửi thành công: {result.sent}\n"
            f"Thất bại: {result.failed}"
        )
