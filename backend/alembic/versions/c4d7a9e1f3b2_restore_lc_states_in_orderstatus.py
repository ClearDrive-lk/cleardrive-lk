"""Restore LC states in orderstatus enum.

Revision ID: c4d7a9e1f3b2
Revises: b1f4c2d9e8aa
Create Date: 2026-03-01 19:05:00.000000
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4d7a9e1f3b2"
down_revision: Union[str, None] = "b1f4c2d9e8aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add LC enum labels required by the LC approval workflow."""
    op.execute(
        "ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'LC_REQUESTED' AFTER 'PAYMENT_CONFIRMED';"
    )
    op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'LC_APPROVED' AFTER 'LC_REQUESTED';")
    op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'LC_REJECTED' AFTER 'LC_APPROVED';")


def downgrade() -> None:
    """Remove LC enum labels by rebuilding the enum type."""
    op.execute(
        """
        CREATE TYPE orderstatus_no_lc AS ENUM (
            'CREATED',
            'PAYMENT_CONFIRMED',
            'ASSIGNED_TO_EXPORTER',
            'SHIPMENT_DOCS_UPLOADED',
            'AWAITING_SHIPMENT_CONFIRMATION',
            'SHIPPED',
            'IN_TRANSIT',
            'ARRIVED_AT_PORT',
            'CUSTOMS_CLEARANCE',
            'DELIVERED',
            'CANCELLED'
        );
        """
    )

    op.execute(
        """
        UPDATE orders
        SET status = 'PAYMENT_CONFIRMED'
        WHERE status::text IN ('LC_REQUESTED', 'LC_APPROVED', 'LC_REJECTED');
        """
    )
    op.execute(
        """
        UPDATE order_status_history
        SET from_status = 'PAYMENT_CONFIRMED'
        WHERE from_status::text IN ('LC_REQUESTED', 'LC_APPROVED', 'LC_REJECTED');
        """
    )
    op.execute(
        """
        UPDATE order_status_history
        SET to_status = 'PAYMENT_CONFIRMED'
        WHERE to_status::text IN ('LC_REQUESTED', 'LC_APPROVED', 'LC_REJECTED');
        """
    )

    op.execute("ALTER TABLE orders ALTER COLUMN status DROP DEFAULT;")

    op.execute(
        """
        ALTER TABLE orders
        ALTER COLUMN status
        TYPE orderstatus_no_lc
        USING status::text::orderstatus_no_lc;
        """
    )
    op.execute(
        """
        ALTER TABLE order_status_history
        ALTER COLUMN from_status
        TYPE orderstatus_no_lc
        USING CASE
            WHEN from_status IS NULL THEN NULL
            ELSE from_status::text::orderstatus_no_lc
        END;
        """
    )
    op.execute(
        """
        ALTER TABLE order_status_history
        ALTER COLUMN to_status
        TYPE orderstatus_no_lc
        USING to_status::text::orderstatus_no_lc;
        """
    )

    op.execute("DROP TYPE orderstatus;")
    op.execute("ALTER TYPE orderstatus_no_lc RENAME TO orderstatus;")
    op.execute("ALTER TABLE orders ALTER COLUMN status SET DEFAULT 'CREATED'::orderstatus;")
