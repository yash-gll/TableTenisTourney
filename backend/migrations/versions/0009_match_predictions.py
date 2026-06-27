"""match_predictions

Revision ID: 0009_match_predictions
Revises: 0008_tournament_registrations
Create Date: 2026-06-27

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_match_predictions"
down_revision: str | None = "0008_tournament_registrations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "match_predictions",
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
            "player_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("player_profiles.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "predicted_winner_team_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("points_awarded", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("match_id", "player_id", name="uq_prediction_match_player"),
    )
    op.create_index("ix_match_predictions_match_id", "match_predictions", ["match_id"])
    op.create_index("ix_match_predictions_tournament_id", "match_predictions", ["tournament_id"])
    op.create_index("ix_match_predictions_player_id", "match_predictions", ["player_id"])


def downgrade() -> None:
    op.drop_table("match_predictions")
