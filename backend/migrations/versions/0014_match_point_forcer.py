"""match_points.forcer_id + forcer_skill (forced errors)

Revision ID: 0014_match_point_forcer
Revises: 0013_match_serve_pairing
Create Date: 2026-06-30

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0014_match_point_forcer"
down_revision: str | None = "0013_match_serve_pairing"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "match_points",
        sa.Column(
            "forcer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("player_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column("match_points", sa.Column("forcer_skill", sa.String(length=40), nullable=True))
    op.create_index("ix_match_points_forcer_id", "match_points", ["forcer_id"])


def downgrade() -> None:
    op.drop_index("ix_match_points_forcer_id", table_name="match_points")
    op.drop_column("match_points", "forcer_skill")
    op.drop_column("match_points", "forcer_id")
