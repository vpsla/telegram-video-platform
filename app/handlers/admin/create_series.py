"""Create-series (playlist) admin flow."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.category_repository import CategoryRepository
from app.database.repositories.series_repository import SeriesRepository
from app.keyboards.admin import category_choice_keyboard
from app.services.series_service import CategoryNotFoundError, DuplicateSlugError, SeriesService
from app.states.create_series import CreateSeriesStates

logger = logging.getLogger(__name__)

router = Router(name="create_series")


@router.message(Command("create_series"))
async def start_create_series(message: Message, state: FSMContext) -> None:
    await state.set_state(CreateSeriesStates.waiting_for_title)
    await message.answer("📚 Nhập <b>tên bộ truyện/series</b>:")


@router.message(CreateSeriesStates.waiting_for_title)
async def receive_series_title(message: Message, state: FSMContext, session: AsyncSession) -> None:
    title = (message.text or "").strip()
    if not title:
        await message.answer("⚠️ Tên không được để trống. Vui lòng nhập lại:")
        return

    await state.update_data(title=title)

    category_repo = CategoryRepository(session)
    categories = await category_repo.list_active()
    if not categories:
        await message.answer("⚠️ Chưa có thể loại nào. Hãy tạo thể loại trước.")
        await state.clear()
        return

    await state.set_state(CreateSeriesStates.waiting_for_category)
    await message.answer(
        "🏷️ Chọn thể loại:",
        reply_markup=category_choice_keyboard(categories, callback_prefix="create_series:category"),
    )


@router.callback_query(
    CreateSeriesStates.waiting_for_category, F.data.startswith("create_series:category:")
)
async def receive_series_category(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.data is None:
        return
    category_id = int(callback.data.split(":")[-1])
    await state.update_data(category_id=category_id)
    await state.set_state(CreateSeriesStates.waiting_for_author)

    if callback.message is not None:
        await callback.message.edit_text("✍️ Nhập <b>tác giả</b> (hoặc /skip để bỏ qua):")
    await callback.answer()


@router.message(Command("skip"), CreateSeriesStates.waiting_for_author)
async def skip_author(message: Message, state: FSMContext) -> None:
    await state.update_data(author=None)
    await state.set_state(CreateSeriesStates.waiting_for_description)
    await message.answer("📝 Nhập <b>mô tả</b> (hoặc /skip để bỏ qua):")


@router.message(CreateSeriesStates.waiting_for_author)
async def receive_author(message: Message, state: FSMContext) -> None:
    await state.update_data(author=(message.text or "").strip() or None)
    await state.set_state(CreateSeriesStates.waiting_for_description)
    await message.answer("📝 Nhập <b>mô tả</b> (hoặc /skip để bỏ qua):")


@router.message(Command("skip"), CreateSeriesStates.waiting_for_description)
async def skip_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=None)
    await state.set_state(CreateSeriesStates.waiting_for_tags)
    await message.answer("🔖 Nhập <b>tags</b>, phân cách bởi dấu phẩy (hoặc /skip):")


@router.message(CreateSeriesStates.waiting_for_description)
async def receive_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=(message.text or "").strip() or None)
    await state.set_state(CreateSeriesStates.waiting_for_tags)
    await message.answer("🔖 Nhập <b>tags</b>, phân cách bởi dấu phẩy (hoặc /skip):")


@router.message(Command("skip"), CreateSeriesStates.waiting_for_tags)
async def skip_tags_and_finish(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await _finish_create_series(message, state, session, tags=None)


@router.message(CreateSeriesStates.waiting_for_tags)
async def receive_tags_and_finish(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    tags = (message.text or "").strip() or None
    await _finish_create_series(message, state, session, tags=tags)


async def _finish_create_series(
    message: Message, state: FSMContext, session: AsyncSession, *, tags: str | None
) -> None:
    data = await state.get_data()
    series_service = SeriesService(SeriesRepository(session), CategoryRepository(session))

    try:
        series = await series_service.create_series(
            category_id=data["category_id"],
            title=data["title"],
            author=data.get("author"),
            description=data.get("description"),
            tags=tags,
        )
    except CategoryNotFoundError:
        await message.answer("⚠️ Thể loại không hợp lệ. Vui lòng thử lại từ /create_series.")
        await state.clear()
        return
    except DuplicateSlugError:
        await message.answer("⚠️ Tên series đã tồn tại (trùng slug). Vui lòng thử lại với tên khác.")
        await state.clear()
        return

    await state.clear()
    await message.answer(
        f"✅ Đã tạo series <b>{series.title}</b> "
        f"(ID: {series.id}, slug: <code>{series.slug}</code>)."
    )
