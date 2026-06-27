"""match_dependencies (bracket QF3/Final wiring)

Revision ID: 0004_match_dependencies
Revises: 0003_matches
Create Date: 2026-06-26

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_match_dependencies"
down_revision: str | None = "0003_matches"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    dependency_slot = postgresql.ENUM("TEAM_A", "TEAM_B", name="dependency_slot")
    dependency_outcome = postgresql.ENUM("WINNER", "LOSER", name="dependency_outcome")

    op.create_table(
        "match_dependencies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "target_match_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("target_slot", dependency_slot, nullable=False),
        sa.Column(
            "source_match_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("source_outcome", dependency_outcome, nullable=False),
    )
    op.create_index("ix_match_dependencies_target", "match_dependencies", ["target_match_id"])
    op.create_index("ix_match_dependencies_source", "match_dependencies", ["source_match_id"])


def downgrade() -> None:
    op.drop_table("match_dependencies")
    for enum_name in ("dependency_outcome", "dependency_slot"):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
