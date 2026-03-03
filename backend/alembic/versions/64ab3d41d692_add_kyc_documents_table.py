"""Adjust kyc_documents for CD-50 fields.

Revision ID: 64ab3d41d692
Revises: 9252d2359f38
Create Date: 2026-02-23 05:05:52.347578
"""

from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "64ab3d41d692"
down_revision: Union[str, None] = "9252d2359f38"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("kyc_documents", sa.Column("gender", sa.String(length=10), nullable=True))
    op.alter_column("kyc_documents", "nic_number", existing_type=sa.VARCHAR(length=255), nullable=True)
    op.alter_column("kyc_documents", "full_name", existing_type=sa.VARCHAR(length=255), nullable=True)
    op.alter_column("kyc_documents", "date_of_birth", existing_type=sa.DATE(), nullable=True)
    op.alter_column("kyc_documents", "address", existing_type=sa.TEXT(), nullable=True)


def downgrade() -> None:
    op.alter_column("kyc_documents", "address", existing_type=sa.TEXT(), nullable=False)
    op.alter_column("kyc_documents", "date_of_birth", existing_type=sa.DATE(), nullable=False)
    op.alter_column("kyc_documents", "full_name", existing_type=sa.VARCHAR(length=255), nullable=False)
    op.alter_column("kyc_documents", "nic_number", existing_type=sa.VARCHAR(length=255), nullable=False)
    op.drop_column("kyc_documents", "gender")
