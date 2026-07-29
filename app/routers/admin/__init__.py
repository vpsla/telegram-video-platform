from aiogram import Router

from app.filters.is_admin import IsAdminFilter
from app.handlers.admin.add_video import router as add_video_router
from app.handlers.admin.attach_episode import router as attach_episode_router
from app.handlers.admin.broadcast import router as broadcast_router
from app.handlers.admin.categories import router as categories_router
from app.handlers.admin.create_series import router as create_series_router
from app.handlers.admin.dashboard import router as dashboard_router
from app.handlers.admin.import_export import router as import_export_router
from app.handlers.admin.menu import router as menu_router
from app.handlers.admin.users import router as users_router

admin_router = Router(name="admin")
admin_router.message.filter(IsAdminFilter())
admin_router.callback_query.filter(IsAdminFilter())

admin_router.include_router(menu_router)
admin_router.include_router(add_video_router)
admin_router.include_router(attach_episode_router)
admin_router.include_router(create_series_router)
admin_router.include_router(categories_router)
admin_router.include_router(users_router)
admin_router.include_router(broadcast_router)
admin_router.include_router(dashboard_router)
admin_router.include_router(import_export_router)

__all__ = ["admin_router"]
