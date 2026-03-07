"""Add PENDING_MANUAL_REVIEW to kycstatus enum.

Revision ID: e4c1a2b3d4f5
Revises: d9a1f2b7c3e4
Create Date: 2026-03-04 16:30:00.000000
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e4c1a2b3d4f5"
down_revision: Union[str, None] = "d9a1f2b7c3e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE kycstatus ADD VALUE IF NOT EXISTS 'PENDING_MANUAL_REVIEW';")


def downgrade() -> None:
    # PostgreSQL enums do not support dropping a value directly in-place.
    # Keeping downgrade as no-op to avoid destructive type rewrite.
    pass
