"""Admin user-management commands: ban / unban / VIP."""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.user_repository import UserRepository
from app.services.admin_user_service import AdminUserService, UserNotFoundError

logger = logging.getLogger(__name__)

router = Router(name="admin_users")


def _parse_telegram_id_and_rest(command: CommandObject) -> tuple[int | None, str]:
    if not command.args:
        return None, ""
    parts = command.args.strip().split(maxsplit=1)
    try:
        telegram_id = int(parts[0])
    except ValueError:
        return None, ""
    rest = parts[1] if len(parts) > 1 else ""
    return telegram_id, rest


@router.message(Command("ban"))
async def ban_user(message: Message, command: CommandObject, session: AsyncSession) -> None:
    telegram_id, reason = _parse_telegram_id_and_rest(command)
    if telegram_id is None:
        await message.answer("Cách dùng: <code>/ban &lt;telegram_id&gt; [lý do]</code>")
        return

    user_repo = UserRepository(session)
    service = AdminUserService(user_repo)
    target = await service.find_by_telegram_id(telegram_id)
    if target is None:
        await message.answer(f"⚠️ Không tìm thấy user với telegram_id={telegram_id}.")
        return

    try:
        await service.ban_user(target.id, reason=reason or "Không có lý do cụ thể")
    except UserNotFoundError:
        await message.answer("⚠️ Không tìm thấy user.")
        return

    await message.answer(f"🚫 Đã khóa user {target.display_name} (telegram_id={telegram_id}).")


@router.message(Command("unban"))
async def unban_user(message: Message, command: CommandObject, session: AsyncSession) -> None:
    if not command.args:
        await message.answer("Cách dùng: <code>/unban &lt;telegram_id&gt;</code>")
        return
    try:
        telegram_id = int(command.args.strip())
    except ValueError:
        await message.answer("⚠️ telegram_id không hợp lệ.")
        return

    user_repo = UserRepository(session)
    service = AdminUserService(user_repo)
    target = await service.find_by_telegram_id(telegram_id)
    if target is None:
        await message.answer(f"⚠️ Không tìm thấy user với telegram_id={telegram_id}.")
        return

    await service.unban_user(target.id)
    await message.answer(f"✅ Đã mở khóa user {target.display_name}.")


@router.message(Command("vip"))
async def grant_vip(message: Message, command: CommandObject, session: AsyncSession) -> None:
    if not command.args:
        await message.answer("Cách dùng: <code>/vip &lt;telegram_id&gt;</code>")
        return
    try:
        telegram_id = int(command.args.strip())
    except ValueError:
        await message.answer("⚠️ telegram_id không hợp lệ.")
        return

    user_repo = UserRepository(session)
    service = AdminUserService(user_repo)
    target = await service.find_by_telegram_id(telegram_id)
    if target is None:
        await message.answer(f"⚠️ Không tìm thấy user với telegram_id={telegram_id}.")
        return

    await service.grant_vip(target.id)
    await message.answer(f"⭐ Đã cấp VIP cho user {target.display_name}.")


@router.message(Command("unvip"))
async def revoke_vip(message: Message, command: CommandObject, session: AsyncSession) -> None:
    if not command.args:
        await message.answer("Cách dùng: <code>/unvip &lt;telegram_id&gt;</code>")
        return
    try:
        telegram_id = int(command.args.strip())
    except ValueError:
        await message.answer("⚠️ telegram_id không hợp lệ.")
        return

    user_repo = UserRepository(session)
    service = AdminUserService(user_repo)
    target = await service.find_by_telegram_id(telegram_id)
    if target is None:
        await message.answer(f"⚠️ Không tìm thấy user với telegram_id={telegram_id}.")
        return

    await service.revoke_vip(target.id)
    await message.answer(f"Đã gỡ VIP của user {target.display_name}.")


@router.message(Command("users"))
async def list_users(message: Message, command: CommandObject, session: AsyncSession) -> None:
    offset = 0
    if command.args and command.args.strip().isdigit():
        offset = int(command.args.strip())

    user_repo = UserRepository(session)
    service = AdminUserService(user_repo)
    users = await service.list_users(offset=offset, limit=10)

    if not users:
        await message.answer("Không có user nào ở trang này.")
        return

    lines = ["👥 <b>Danh sách user:</b>\n"]
    for u in users:
        flags = []
        if u.is_admin:
            flags.append("👑admin")
        if u.is_currently_vip:
            flags.append("⭐vip")
        if u.is_banned:
            flags.append("🚫banned")
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        lines.append(f"• {u.display_name} (id={u.telegram_id}){flag_str}")
    lines.append(f"\nDùng <code>/users {offset + 10}</code> để xem trang tiếp theo.")
    await message.answer("\n".join(lines))
