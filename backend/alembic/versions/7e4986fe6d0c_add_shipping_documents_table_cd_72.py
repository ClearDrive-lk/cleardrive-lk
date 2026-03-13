"""Add shipping documents table (CD-72)

Revision ID: 7e4986fe6d0c
Revises: 1a72b73c14a4
Create Date: 2026-03-10 19:56:21.454035

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '7e4986fe6d0c'
down_revision: Union[str, None] = '1a72b73c14a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'documenttype') THEN
                    ALTER TYPE documenttype ADD VALUE IF NOT EXISTS 'BILL_OF_LADING';
                    ALTER TYPE documenttype ADD VALUE IF NOT EXISTS 'BILL_OF_LANDING';
                END IF;
            END
            $$;
            """
        )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_name = 'shipping_documents'
            ) THEN
                UPDATE shipping_documents
                SET document_type = 'BILL_OF_LADING'
                WHERE document_type = 'BILL_OF_LANDING';
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    # Postgres enums do not support removing values safely in downgrade.
    pass
