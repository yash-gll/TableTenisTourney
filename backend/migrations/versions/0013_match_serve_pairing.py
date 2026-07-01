"""matches.serve_pairing

Revision ID: 0013_match_serve_pairing
Revises: 0012_tournament_exhibition
Create Date: 2026-06-30

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013_match_serve_pairing"
down_revision: str | None = "0012_tournament_exhibition"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("matches", sa.Column("serve_pairing", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("matches", "serve_pairing")
