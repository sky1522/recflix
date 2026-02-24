"""initial schema snapshot

Revision ID: e2b032d303d8
Revises:
Create Date: 2026-02-24 16:20:17.871918

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = 'e2b032d303d8'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Baseline — existing schema already in place. Stamp only."""


def downgrade() -> None:
    """No downgrade for baseline."""
