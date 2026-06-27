"""rating_events, rating_snapshots, rating_config

Revision ID: 0005_ratings
Revises: 0004_match_dependencies
Create Date: 2026-06-26

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_ratings"
down_revision: str | None = "0004_match_dependencies"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    rating_event_type = postgresql.ENUM(
        "MATCH_RESULT",
        "MATCH_CORRECTION_REVERSAL",
        "MATCH_CORRECTION_REAPPLY",
        "TOURNAMENT_PLACEMENT_BONUS",
        "ADMIN_ADJUSTMENT",
        "SEASON_RESET",
        name="rating_event_type",
    )
    snapshot_type = postgresql.ENUM("TOURNAMENT_START", "TOURNAMENT_END", name="snapshot_type")

    op.create_table(
        "rating_config",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("starting_rating", sa.Integer(), nullable=False, server_default="1000"),
        sa.Column("rating_floor", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("group_k", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("qf1_k", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("qf2_k", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("qf3_k", sa.Integer(), nullable=False, server_default="28"),
        sa.Column("final_k", sa.Integer(), nullable=False, server_default="32"),
        sa.Column("champion_bonus", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("runner_up_bonus", sa.Integer(), nullable=False, server_default="15"),
        sa.Column("third_place_bonus", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "rating_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "player_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("player_profiles.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "tournament_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=True
        ),
        sa.Column(
            "match_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("matches.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("event_type", rating_event_type, nullable=False),
        sa.Column("rating_before", sa.Integer(), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("rating_after", sa.Integer(), nullable=False),
        sa.Column("calculation_data", postgresql.JSONB(), nullable=True),
        sa.Column("sequence_number", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_superseded", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("superseded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_rating_events_player_id", "rating_events", ["player_id"])
    op.create_index("ix_rating_events_tournament_id", "rating_events", ["tournament_id"])

    op.create_table(
        "rating_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "player_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("player_profiles.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "tournament_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("snapshot_type", snapshot_type, nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_rating_snapshots_player_id", "rating_snapshots", ["player_id"])
    op.create_index("ix_rating_snapshots_tournament_id", "rating_snapshots", ["tournament_id"])


def downgrade() -> None:
    op.drop_table("rating_snapshots")
    op.drop_table("rating_events")
    op.drop_table("rating_config")
    for enum_name in ("snapshot_type", "rating_event_type"):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
