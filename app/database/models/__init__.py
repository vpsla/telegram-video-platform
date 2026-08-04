"""
Central import point for all ORM models.

Alembic's env.py imports this module so that Base.metadata is fully
populated before autogenerate compares it against the live database.
Every new model module added in later phases must be imported here.

Import order matters for forward-reference resolution: Category before
Series before Video before Episode; User must exist before
Favorite/History/WatchProgress/Notification/View.
"""

from app.database.models.category import Category
from app.database.models.episode import Episode
from app.database.models.favorite import Favorite
from app.database.models.history import History
from app.database.models.notification import Notification, NotificationType
from app.database.models.series import Series
from app.database.models.settings import Settings
from app.database.models.user import User
from app.database.models.video import Video
from app.database.models.view import View
from app.database.models.watch_progress import WatchProgress

__all__ = [
    "Category",
    "Episode",
    "Favorite",
    "History",
    "Notification",
    "NotificationType",
    "Series",
    "Settings",
    "User",
    "Video",
    "View",
    "WatchProgress",
]
