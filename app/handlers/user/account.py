"""Account info handler ("Thông tin tài khoản")."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.database.models.user import User

logger = logging.getLogger(__name__)

router = Router(name="account")


def _format_watch_time(total_seconds: int) -> str:
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    if hours > 0:
        return f"{hours} giờ {minutes} phút"
    return f"{minutes} phút"


@router.callback_query(F.data == "account:info")
async def show_account_info(callback: CallbackQuery, user: User) -> None:
    vip_status = "⭐ VIP" if user.is_currently_vip else "Thường"
    vip_expiry = ""
    if user.is_currently_vip and user.vip_expires_at is not None:
        vip_expiry = f" (hết hạn: {user.vip_expires_at:%d/%m/%Y})"

    text = (
        f"👤 <b>Thông tin tài khoản</b>\n\n"
        f"Tên: {user.display_name}\n"
        f"Hạng: {vip_status}{vip_expiry}\n"
        f"⏱️ Tổng thời gian xem: {_format_watch_time(user.total_watch_seconds)}\n"
        f"📅 Tham gia từ: {user.created_at:%d/%m/%Y}"
    )
    if callback.message is not None:
        await callback.message.edit_text(text)
    await callback.answer()
