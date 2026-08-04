from app.keyboards.admin import admin_main_menu_keyboard, category_choice_keyboard
from app.keyboards.common import confirm_cancel_keyboard, pagination_keyboard
from app.keyboards.user import (
    category_list_keyboard,
    home_menu_keyboard,
    series_detail_keyboard,
    series_list_keyboard,
    video_list_keyboard,
)

__all__ = [
    "admin_main_menu_keyboard",
    "category_choice_keyboard",
    "category_list_keyboard",
    "confirm_cancel_keyboard",
    "home_menu_keyboard",
    "pagination_keyboard",
    "series_detail_keyboard",
    "series_list_keyboard",
    "video_list_keyboard",
]
