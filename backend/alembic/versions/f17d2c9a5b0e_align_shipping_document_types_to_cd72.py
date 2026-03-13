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
    # Create a new enum with the CD-72 document types.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'documenttype_new') THEN
                DROP TYPE documenttype_new;
            END IF;
        END
        $$;
        """
    )
    op.execute(
        """
        CREATE TYPE documenttype_new AS ENUM (
            'BILL_OF_LADING',
            'COMMERCIAL_INVOICE',
            'PACKING_LIST',
            'CUSTOMS_DECLARATION',
            'CERTIFICATE_OF_ORIGIN',
            'CONTAINER_PHOTO',
            'OTHER'
        );
        """
    )

    # Map old values to new types before altering the column.
    op.execute(
        """
        UPDATE shipping_documents
        SET document_type = CASE document_type::text
            WHEN 'BILL_OF_LANDING' THEN 'BILL_OF_LADING'
            WHEN 'EXPORT_CERTIFICATE' THEN 'CERTIFICATE_OF_ORIGIN'
            WHEN 'INSURANCE_CERTIFICATE' THEN 'OTHER'
            ELSE document_type::text
        END
        WHERE document_type::text IN (
            'BILL_OF_LANDING',
            'EXPORT_CERTIFICATE',
            'INSURANCE_CERTIFICATE'
        );
        """
    )

    op.execute(
        """
        ALTER TABLE shipping_documents
        ALTER COLUMN document_type TYPE documenttype_new
        USING (
            CASE document_type::text
                WHEN 'BILL_OF_LANDING' THEN 'BILL_OF_LADING'
                WHEN 'EXPORT_CERTIFICATE' THEN 'CERTIFICATE_OF_ORIGIN'
                WHEN 'INSURANCE_CERTIFICATE' THEN 'OTHER'
                ELSE document_type::text
            END
        )::documenttype_new;
        """
    )

    op.execute("DROP TYPE documenttype;")
    op.execute("ALTER TYPE documenttype_new RENAME TO documenttype;")


def downgrade() -> None:
    # Postgres enums do not support removing values safely in downgrade.
    pass
