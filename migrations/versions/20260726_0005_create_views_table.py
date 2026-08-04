"""create views table

Revision ID: 20260726_0005
Revises: 20260726_0004
Create Date: 2026-07-26 20:00:00

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260726_0005"
down_revision: Union[str, None] = "20260726_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "views",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "video_id",
            sa.Integer(),
            sa.ForeignKey("videos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_views_video_created", "views", ["video_id", "created_at"])
    op.create_index("ix_views_created_at", "views", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_views_created_at", table_name="views")
    op.drop_index("ix_views_video_created", table_name="views")
    op.drop_table("views")
