"""Ensure shipping_documents.sha256_hash exists.

Revision ID: b5c7d9e1f2a3
Revises: ea78ccc57cfe
Create Date: 2026-03-20 23:55:00.000000
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b5c7d9e1f2a3"
down_revision: Union[str, None] = "ea78ccc57cfe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Some environments reached later revisions before CD-72.4 was inserted
    # into the middle of the chain. This idempotent guard fixes that drift.
    op.execute(
        """
        ALTER TABLE shipping_documents
        ADD COLUMN IF NOT EXISTS sha256_hash VARCHAR(64)
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE shipping_documents
        DROP COLUMN IF EXISTS sha256_hash
        """
    )
