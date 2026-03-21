"""Align shipping document types to CD-72 spec.

Revision ID: f17d2c9a5b0e
Revises: 7e4986fe6d0c
Create Date: 2026-03-12 10:15:00.000000
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f17d2c9a5b0e"
down_revision: Union[str, None] = "7e4986fe6d0c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Current application models still use EXPORT_CERTIFICATE and
    # INSURANCE_CERTIFICATE, so this revision only normalizes the legacy
    # BILL_OF_LANDING value to BILL_OF_LADING.
    op.execute(
        """
        UPDATE shipping_documents
        SET document_type = 'BILL_OF_LADING'::documenttype
        WHERE document_type::text = 'BILL_OF_LANDING';
        """
    )


def downgrade() -> None:
    # Postgres enums do not support removing values safely in downgrade.
    pass
