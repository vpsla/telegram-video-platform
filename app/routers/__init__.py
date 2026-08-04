from aiogram import Router

from app.routers.admin import admin_router
from app.routers.user import user_router

main_router = Router(name="main")
main_router.include_router(user_router)
main_router.include_router(admin_router)

__all__ = ["main_router"]
