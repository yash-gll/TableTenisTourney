"""match_points.kind (WIN | FAULT)

Revision ID: 0011_match_point_kind
Revises: 0010_match_points
Create Date: 2026-06-30

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011_match_point_kind"
down_revision: str | None = "0010_match_points"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "match_points",
        sa.Column("kind", sa.String(length=8), nullable=False, server_default="WIN"),
    )


def downgrade() -> None:
    op.drop_column("match_points", "kind")
