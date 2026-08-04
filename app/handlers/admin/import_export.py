"""Export/import data (CSV) admin flow."""

from __future__ import annotations

import io
import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Document, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.category_repository import CategoryRepository
from app.database.repositories.series_repository import SeriesRepository
from app.services.import_export_service import ImportExportService
from app.services.series_service import SeriesService

logger = logging.getLogger(__name__)

router = Router(name="import_export")


def _build_service(session: AsyncSession) -> ImportExportService:
    series_repo = SeriesRepository(session)
    category_repo = CategoryRepository(session)
    series_service = SeriesService(series_repo, category_repo)
    return ImportExportService(series_repo, category_repo, series_service)


@router.message(Command("export_series"))
async def export_series(message: Message, session: AsyncSession) -> None:
    service = _build_service(session)
    csv_content = await service.export_series_csv()

    file = BufferedInputFile(csv_content.encode("utf-8-sig"), filename="series_export.csv")
    await message.answer_document(file, caption="📤 Export danh sách series (CSV).")


@router.message(Command("import_series"))
async def prompt_import_series(message: Message) -> None:
    await message.answer(
        "📥 Gửi file CSV để import series.\n\n"
        "Cột bắt buộc: <code>title</code>, <code>category_slug</code>\n"
        "Cột tùy chọn: <code>slug</code>, <code>author</code>, "
        "<code>description</code>, <code>tags</code>"
    )


@router.message(lambda m: m.document is not None and m.caption == "/import_series")
async def handle_import_series_document(message: Message, session: AsyncSession) -> None:
    document: Document = message.document  # type: ignore[assignment]
    if not document.file_name or not document.file_name.lower().endswith(".csv"):
        await message.answer("⚠️ Vui lòng gửi file .csv.")
        return

    file_bytes = await message.bot.download(document.file_id)
    if file_bytes is None:
        await message.answer("⚠️ Không thể tải file.")
        return

    raw = file_bytes.read() if isinstance(file_bytes, io.BytesIO) else file_bytes
    csv_content = raw.decode("utf-8-sig")

    service = _build_service(session)
    result = await service.import_series_csv(csv_content)

    summary = (
        f"📥 <b>Kết quả import:</b>\n\n"
        f"✅ Đã tạo: {result.created}\n"
        f"⏭️ Bỏ qua: {result.skipped}\n"
    )
    if result.errors:
        error_lines = "\n".join(f"- Dòng {e.row_number}: {e.message}" for e in result.errors[:10])
        summary += f"\n<b>Lỗi (tối đa 10 dòng đầu):</b>\n{error_lines}"

    await message.answer(summary)
