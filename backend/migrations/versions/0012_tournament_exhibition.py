"""tournaments.is_exhibition

Revision ID: 0012_tournament_exhibition
Revises: 0011_match_point_kind
Create Date: 2026-06-30

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012_tournament_exhibition"
down_revision: str | None = "0011_match_point_kind"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tournaments",
        sa.Column("is_exhibition", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("tournaments", "is_exhibition")
