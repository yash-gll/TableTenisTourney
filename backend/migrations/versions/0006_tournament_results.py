"""tournament_results

Revision ID: 0006_tournament_results
Revises: 0005_ratings
Create Date: 2026-06-26

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_tournament_results"
down_revision: str | None = "0005_ratings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tournament_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tournament_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False, unique=True
        ),
        sa.Column("champion_team_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("runner_up_team_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("third_place_team_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("fourth_place_team_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("final_group_leaderboard", postgresql.JSONB(), nullable=True),
        sa.Column("final_bracket", postgresql.JSONB(), nullable=True),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finalized_by", postgresql.UUID(as_uuid=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("tournament_results")
