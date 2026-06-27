"""player_profiles.skill_ratings

Revision ID: 0007_skill_ratings
Revises: 0006_tournament_results
Create Date: 2026-06-27

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_skill_ratings"
down_revision: str | None = "0006_tournament_results"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "player_profiles",
        sa.Column("skill_ratings", postgresql.JSONB(), nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_column("player_profiles", "skill_ratings")
