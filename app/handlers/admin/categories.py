"""Category management admin flow."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.category_repository import CategoryRepository
from app.services.series_service import slugify
from app.states.manage_category import ManageCategoryStates

logger = logging.getLogger(__name__)

router = Router(name="manage_category")


@router.message(Command("categories"))
async def list_categories(message: Message, session: AsyncSession) -> None:
    repo = CategoryRepository(session)
    categories = await repo.list_all()

    if not categories:
        await message.answer("Chưa có thể loại nào. Dùng /add_category để tạo thể loại đầu tiên.")
        return

    lines = ["🏷️ <b>Danh sách thể loại:</b>\n"]
    for c in categories:
        status = "✅" if c.is_active else "🚫"
        lines.append(f"{status} {c.icon_emoji or ''} {c.name} (<code>{c.slug}</code>)")
    lines.append("\nDùng /add_category để thêm mới.")
    await message.answer("\n".join(lines))


@router.message(Command("add_category"))
async def start_add_category(message: Message, state: FSMContext) -> None:
    await state.set_state(ManageCategoryStates.waiting_for_name)
    await message.answer("🏷️ Nhập <b>tên thể loại</b> mới (ví dụ: Tiên Hiệp):")


@router.message(ManageCategoryStates.waiting_for_name)
async def receive_category_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("⚠️ Tên không được để trống. Vui lòng nhập lại:")
        return

    await state.update_data(name=name)
    await state.set_state(ManageCategoryStates.waiting_for_icon)
    await message.answer("😀 Gửi một <b>emoji</b> đại diện cho thể loại (hoặc /skip để bỏ qua):")


@router.message(Command("skip"), ManageCategoryStates.waiting_for_icon)
async def skip_icon_and_finish(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await _finish_add_category(message, state, session, icon=None)


@router.message(ManageCategoryStates.waiting_for_icon)
async def receive_icon_and_finish(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    icon = (message.text or "").strip() or None
    await _finish_add_category(message, state, session, icon=icon)


async def _finish_add_category(
    message: Message, state: FSMContext, session: AsyncSession, *, icon: str | None
) -> None:
    data = await state.get_data()
    repo = CategoryRepository(session)

    slug = slugify(data["name"])
    if await repo.get_by_slug(slug) is not None:
        await message.answer(f"⚠️ Thể loại với slug <code>{slug}</code> đã tồn tại.")
        await state.clear()
        return

    category = await repo.create(name=data["name"], slug=slug, icon_emoji=icon)
    await state.clear()
    await message.answer(
        f"✅ Đã tạo thể loại <b>{category.name}</b> (slug: <code>{category.slug}</code>)."
    )


@router.callback_query(F.data.startswith("category:toggle:"))
async def toggle_category_active(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.data is None:
        return
    category_id = int(callback.data.split(":")[-1])
    repo = CategoryRepository(session)
    category = await repo.get_by_id(category_id)
    if category is None:
        await callback.answer("Không tìm thấy thể loại.", show_alert=True)
        return

    await repo.set_active(category_id, active=not category.is_active)
    await callback.answer("Đã cập nhật trạng thái thể loại.")
