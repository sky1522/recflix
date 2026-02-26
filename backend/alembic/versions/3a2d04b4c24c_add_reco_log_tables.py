"""add_reco_log_tables

Revision ID: 3a2d04b4c24c
Revises: e2b032d303d8
Create Date: 2026-02-26

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3a2d04b4c24c"
down_revision: str | None = "e2b032d303d8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # reco_impressions
    op.create_table(
        "reco_impressions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("session_id", sa.String(64), nullable=True),
        sa.Column("experiment_group", sa.String(16), nullable=False),
        sa.Column("algorithm_version", sa.String(64), nullable=False),
        sa.Column("section", sa.String(32), nullable=False),
        sa.Column("movie_id", sa.Integer(), nullable=False),
        sa.Column("rank", sa.SmallInteger(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("context", postgresql.JSONB(), nullable=True),
        sa.Column(
            "served_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_imp_request", "reco_impressions", ["request_id"])
    op.create_index("idx_imp_user_time", "reco_impressions", ["user_id", "served_at"])
    op.create_index(
        "idx_imp_algo", "reco_impressions", ["algorithm_version", "served_at"]
    )

    # reco_interactions
    op.create_table(
        "reco_interactions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("session_id", sa.String(64), nullable=True),
        sa.Column("movie_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("dwell_ms", sa.Integer(), nullable=True),
        sa.Column("position", sa.SmallInteger(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column(
            "interacted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_int_request", "reco_interactions", ["request_id"])
    op.create_index(
        "idx_int_user_time", "reco_interactions", ["user_id", "interacted_at"]
    )
    op.create_index(
        "idx_int_movie", "reco_interactions", ["movie_id", "event_type"]
    )

    # reco_judgments
    op.create_table(
        "reco_judgments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("movie_id", sa.Integer(), nullable=False),
        sa.Column("label_type", sa.String(16), nullable=False),
        sa.Column("label_value", sa.Float(), nullable=False),
        sa.Column(
            "judged_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_jdg_user", "reco_judgments", ["user_id", "judged_at"])
    op.create_index("idx_jdg_request", "reco_judgments", ["request_id"])


def downgrade() -> None:
    op.drop_table("reco_judgments")
    op.drop_table("reco_interactions")
    op.drop_table("reco_impressions")
