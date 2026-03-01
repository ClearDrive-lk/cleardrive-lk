"""Align orderstatus enum to CD-31 11-state model.

Revision ID: b1f4c2d9e8aa
Revises: 13e4f8c8fc37
Create Date: 2026-03-01 18:40:00.000000
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b1f4c2d9e8aa"
down_revision: Union[str, None] = "13e4f8c8fc37"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Remove deprecated LC_* enum values and align DB enum with application enum.

    Mapping chosen for backward compatibility:
    - LC_REQUESTED -> PAYMENT_CONFIRMED
    - LC_APPROVED  -> PAYMENT_CONFIRMED
    - LC_REJECTED  -> PAYMENT_CONFIRMED
    """
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

    op.execute(
        """
        CREATE TYPE orderstatus_new AS ENUM (
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

    op.execute("ALTER TABLE orders ALTER COLUMN status DROP DEFAULT;")

    op.execute(
        """
        ALTER TABLE orders
        ALTER COLUMN status
        TYPE orderstatus_new
        USING status::text::orderstatus_new;
        """
    )
    op.execute(
        """
        ALTER TABLE order_status_history
        ALTER COLUMN from_status
        TYPE orderstatus_new
        USING CASE
            WHEN from_status IS NULL THEN NULL
            ELSE from_status::text::orderstatus_new
        END;
        """
    )
    op.execute(
        """
        ALTER TABLE order_status_history
        ALTER COLUMN to_status
        TYPE orderstatus_new
        USING to_status::text::orderstatus_new;
        """
    )

    op.execute("DROP TYPE orderstatus;")
    op.execute("ALTER TYPE orderstatus_new RENAME TO orderstatus;")
    op.execute("ALTER TABLE orders ALTER COLUMN status SET DEFAULT 'CREATED'::orderstatus;")


def downgrade() -> None:
    """Restore historical orderstatus enum including LC_* values."""
    op.execute(
        """
        CREATE TYPE orderstatus_old AS ENUM (
            'CREATED',
            'PAYMENT_CONFIRMED',
            'LC_REQUESTED',
            'LC_APPROVED',
            'LC_REJECTED',
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

    op.execute("ALTER TABLE orders ALTER COLUMN status DROP DEFAULT;")

    op.execute(
        """
        ALTER TABLE orders
        ALTER COLUMN status
        TYPE orderstatus_old
        USING status::text::orderstatus_old;
        """
    )
    op.execute(
        """
        ALTER TABLE order_status_history
        ALTER COLUMN from_status
        TYPE orderstatus_old
        USING CASE
            WHEN from_status IS NULL THEN NULL
            ELSE from_status::text::orderstatus_old
        END;
        """
    )
    op.execute(
        """
        ALTER TABLE order_status_history
        ALTER COLUMN to_status
        TYPE orderstatus_old
        USING to_status::text::orderstatus_old;
        """
    )

    op.execute("DROP TYPE orderstatus;")
    op.execute("ALTER TYPE orderstatus_old RENAME TO orderstatus;")
    op.execute("ALTER TABLE orders ALTER COLUMN status SET DEFAULT 'CREATED'::orderstatus;")
