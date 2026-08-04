from aiogram import Router

from app.handlers.user.account import router as account_router
from app.handlers.user.browse import router as browse_router
from app.handlers.user.favorites import router as favorites_router
from app.handlers.user.history import router as history_router
from app.handlers.user.home import router as home_router
from app.handlers.user.search import router as search_router
from app.handlers.user.start import router as start_router
from app.handlers.user.watch import router as watch_router
<<<<<<< HEAD
from app.handlers.user.web_app_data import router as web_app_data_router
=======
>>>>>>> aa711cf084e31aa3c44790aacdffc3901927f779

user_router = Router(name="user")
user_router.include_router(start_router)
user_router.include_router(home_router)
user_router.include_router(browse_router)
user_router.include_router(watch_router)
user_router.include_router(search_router)
user_router.include_router(history_router)
user_router.include_router(favorites_router)
user_router.include_router(account_router)
<<<<<<< HEAD
user_router.include_router(web_app_data_router)
=======
>>>>>>> aa711cf084e31aa3c44790aacdffc3901927f779

__all__ = ["user_router"]
