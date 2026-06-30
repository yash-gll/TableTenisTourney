"""match_points + player_profiles.skill_overrides

Revision ID: 0010_match_points
Revises: 0009_match_predictions
Create Date: 2026-06-27

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010_match_points"
down_revision: str | None = "0009_match_predictions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "player_profiles",
        sa.Column("skill_overrides", postgresql.JSONB(), nullable=False, server_default="{}"),
    )
    op.create_table(
        "match_points",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "match_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "tournament_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "team_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "player_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("player_profiles.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("skill", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_match_points_match_id", "match_points", ["match_id"])
    op.create_index("ix_match_points_tournament_id", "match_points", ["tournament_id"])
    op.create_index("ix_match_points_player_id", "match_points", ["player_id"])


def downgrade() -> None:
    op.drop_table("match_points")
    op.drop_column("player_profiles", "skill_overrides")
