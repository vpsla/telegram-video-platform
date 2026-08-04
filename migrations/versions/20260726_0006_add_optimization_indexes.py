"""add optimization indexes to videos and series

Revision ID: 20260726_0006
Revises: 20260726_0005
Create Date: 2026-07-26 21:00:00

These indexes target columns that are filtered on in every hot-path
listing query (Trang chủ, Video mới, Video nổi bật, danh sách theo
thể loại) but were missing an index up to this point — added here as
a dedicated "Optimization" migration per the Phase 6 spec, separate
from the Views table migration so each migration has one clear intent.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260726_0006"
down_revision: Union[str, None] = "20260726_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_videos_category_id", "videos", ["category_id"])
    op.create_index("ix_videos_is_hidden", "videos", ["is_hidden"])
    op.create_index("ix_series_is_hidden", "series", ["is_hidden"])
    op.create_index("ix_series_is_featured", "series", ["is_featured"])


def downgrade() -> None:
    op.drop_index("ix_series_is_featured", table_name="series")
    op.drop_index("ix_series_is_hidden", table_name="series")
    op.drop_index("ix_videos_is_hidden", table_name="videos")
    op.drop_index("ix_videos_category_id", table_name="videos")
