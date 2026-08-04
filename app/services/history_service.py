"""
History / watch-progress service.

Two concerns are coordinated here because they're always updated
together from the playback flow:
  - History: an append-only log entry per watch event ("Lịch sử").
  - WatchProgress: the single latest resume position ("Tiếp tục xem").

Kept as one service (rather than two independent ones) so handlers
never forget to update one when they update the other.
"""

from __future__ import annotations

from app.database.models.history import History
from app.database.models.video import Video
from app.database.models.watch_progress import WatchProgress
from app.database.repositories.history_repository import HistoryRepository
from app.database.repositories.watch_progress_repository import WatchProgressRepository


class HistoryService:
    def __init__(
        self,
        history_repo: HistoryRepository,
        watch_progress_repo: WatchProgressRepository,
    ) -> None:
        self._history_repo = history_repo
        self._watch_progress_repo = watch_progress_repo

    async def record_watch_start(self, *, user_id: int, video_id: int) -> History:
        """Called once when the video is delivered to the user (i.e. right
        after VideoService.send_video_to_user succeeds)."""
        return await self._history_repo.record(user_id=user_id, video_id=video_id)

    async def update_progress(
        self,
        *,
        user_id: int,
        video_id: int,
        position_seconds: int,
        is_completed: bool = False,
    ) -> WatchProgress:
        """Called periodically (or on 'mark as watched') to update resume
        position. Does not touch History — a scrub/seek isn't a new
        watch event."""
        return await self._watch_progress_repo.upsert(
            user_id=user_id,
            video_id=video_id,
            position_seconds=position_seconds,
            is_completed=is_completed,
        )

    async def get_continue_watching(self, user_id: int, *, limit: int = 10) -> list[WatchProgress]:
        return await self._watch_progress_repo.list_continue_watching(user_id, limit=limit)

    async def get_history(self, user_id: int, *, offset: int = 0, limit: int = 20) -> list[History]:
        return await self._history_repo.list_for_user(user_id, offset=offset, limit=limit)

    async def clear_history(self, user_id: int) -> int:
        return await self._history_repo.clear_for_user(user_id)

    async def get_continue_watching_videos(self, user_id: int, *, limit: int = 10) -> list[Video]:
        """Convenience accessor returning just the Video objects, in case
        a handler only needs the video list (e.g. rendering thumbnails)
        without the raw progress metadata."""
        entries = await self.get_continue_watching(user_id, limit=limit)
        return [entry.video for entry in entries]
