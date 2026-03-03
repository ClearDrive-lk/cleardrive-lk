"""Compatibility no-op revision to keep a single Alembic head.

Revision ID: 13e4f8c8fc37
Revises: 9f5e2b1c4d77
Create Date: 2026-02-20 18:22:08.733222
"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "13e4f8c8fc37"
down_revision: Union[str, None] = "9f5e2b1c4d77"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op compatibility migration."""


def downgrade() -> None:
    """No-op compatibility migration."""
