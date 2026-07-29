"""Search handler for regular users."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.category_repository import CategoryRepository
from app.database.repositories.series_repository import SeriesRepository
from app.keyboards.user import series_list_keyboard
from app.services.search_service import SearchService
from app.states.search import SearchStates

logger = logging.getLogger(__name__)

router = Router(name="search")


@router.callback_query(F.data == "search:prompt")
async def prompt_search(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SearchStates.waiting_for_query)
    if callback.message is not None:
        await callback.message.edit_text(
            "🔎 Nhập từ khóa tìm kiếm (tên truyện, tác giả, hoặc tag):"
        )
    await callback.answer()


@router.message(SearchStates.waiting_for_query)
async def receive_search_query(message: Message, state: FSMContext, session: AsyncSession) -> None:
    query = (message.text or "").strip()
    await state.clear()

    if not query:
        await message.answer("⚠️ Từ khóa không được để trống.")
        return

    service = SearchService(SeriesRepository(session), CategoryRepository(session))
    results = await service.search_by_keyword(query, limit=8)

    if not results:
        await message.answer(f"🔎 Không tìm thấy kết quả nào cho: <b>{query}</b>")
        return

    keyboard = series_list_keyboard(results, offset=0, limit=8, callback_prefix="search:noop")
    await message.answer(f"🔎 <b>Kết quả tìm kiếm cho:</b> {query}", reply_markup=keyboard)
