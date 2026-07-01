"""match_points.detail (specific fault type)

Revision ID: 0016_match_point_detail
Revises: 0015_match_first_server
Create Date: 2026-06-30

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016_match_point_detail"
down_revision: str | None = "0015_match_first_server"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("match_points", sa.Column("detail", sa.String(length=40), nullable=True))


def downgrade() -> None:
    op.drop_column("match_points", "detail")
