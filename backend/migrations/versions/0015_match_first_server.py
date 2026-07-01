"""matches.first_server_id

Revision ID: 0015_match_first_server
Revises: 0014_match_point_forcer
Create Date: 2026-06-30

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0015_match_first_server"
down_revision: str | None = "0014_match_point_forcer"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "matches",
        sa.Column(
            "first_server_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("player_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("matches", "first_server_id")
