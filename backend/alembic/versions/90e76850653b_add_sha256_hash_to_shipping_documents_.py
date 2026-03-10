"""Add sha256_hash to shipping_documents (CD-72.4)

Revision ID: 90e76850653b
Revises: 7e4986fe6d0c
Create Date: 2026-03-10 20:36:27.064113

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '90e76850653b'
down_revision: Union[str, None] = '7e4986fe6d0c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE shipping_documents ADD COLUMN IF NOT EXISTS sha256_hash VARCHAR(64)"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE shipping_documents DROP COLUMN IF EXISTS sha256_hash")
