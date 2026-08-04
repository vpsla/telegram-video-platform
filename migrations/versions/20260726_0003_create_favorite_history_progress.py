"""create favorites, history, watch_progress tables

Revision ID: 20260726_0003
Revises: 20260726_0002
Create Date: 2026-07-26 14:00:00

"""

from __future__ import annotations

<<<<<<< HEAD
from typing import Sequence, Union
=======
from collections.abc import Sequence
>>>>>>> aa711cf084e31aa3c44790aacdffc3901927f779

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260726_0003"
<<<<<<< HEAD
down_revision: Union[str, None] = "20260726_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
=======
down_revision: str | None = "20260726_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
>>>>>>> aa711cf084e31aa3c44790aacdffc3901927f779


def upgrade() -> None:
    # --- favorites --------------------------------------------------------
    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "series_id",
            sa.Integer(),
            sa.ForeignKey("series.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
<<<<<<< HEAD
    op.create_index(
        "ix_favorites_user_series", "favorites", ["user_id", "series_id"], unique=True
    )
=======
    op.create_index("ix_favorites_user_series", "favorites", ["user_id", "series_id"], unique=True)
>>>>>>> aa711cf084e31aa3c44790aacdffc3901927f779
    op.create_index("ix_favorites_series_id", "favorites", ["series_id"])

    # --- history ------------------------------------------------------------
    op.create_table(
        "history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "video_id",
            sa.Integer(),
            sa.ForeignKey("videos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_history_user_created", "history", ["user_id", "created_at"])
    op.create_index("ix_history_video_id", "history", ["video_id"])

    # --- watch_progress -------------------------------------------------------
    op.create_table(
        "watch_progress",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "video_id",
            sa.Integer(),
            sa.ForeignKey("videos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_watch_progress_user_video", "watch_progress", ["user_id", "video_id"], unique=True
    )
<<<<<<< HEAD
    op.create_index(
        "ix_watch_progress_user_updated", "watch_progress", ["user_id", "updated_at"]
    )
=======
    op.create_index("ix_watch_progress_user_updated", "watch_progress", ["user_id", "updated_at"])
>>>>>>> aa711cf084e31aa3c44790aacdffc3901927f779


def downgrade() -> None:
    op.drop_index("ix_watch_progress_user_updated", table_name="watch_progress")
    op.drop_index("ix_watch_progress_user_video", table_name="watch_progress")
    op.drop_table("watch_progress")

    op.drop_index("ix_history_video_id", table_name="history")
    op.drop_index("ix_history_user_created", table_name="history")
    op.drop_table("history")

    op.drop_index("ix_favorites_series_id", table_name="favorites")
    op.drop_index("ix_favorites_user_series", table_name="favorites")
    op.drop_table("favorites")
