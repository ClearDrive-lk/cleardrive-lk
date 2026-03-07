"""Sync payments schema with PayHere flow

Revision ID: 9f5e2b1c4d77
Revises: 568d2128ae73
Create Date: 2026-02-22 14:20:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9f5e2b1c4d77"
down_revision: Union[str, None] = "568d2128ae73"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure payment status enum contains PROCESSING (idempotent for reruns)
    op.execute(
        """
        DO $$
        BEGIN
            ALTER TYPE paymentstatus ADD VALUE IF NOT EXISTS 'PROCESSING';
        EXCEPTION
            WHEN undefined_object THEN NULL;
        END $$;
        """
    )

    # Add PayHere-specific columns used by payment routes
    op.execute("ALTER TABLE payments ADD COLUMN IF NOT EXISTS payhere_order_id VARCHAR(255);")
    op.execute("ALTER TABLE payments ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50);")
    op.execute("ALTER TABLE payments ADD COLUMN IF NOT EXISTS card_holder_name VARCHAR(255);")
    op.execute("ALTER TABLE payments ADD COLUMN IF NOT EXISTS card_no VARCHAR(20);")

    # Keep amount precision aligned with model
    op.execute("ALTER TABLE payments ALTER COLUMN amount TYPE NUMERIC(12, 2);")


def downgrade() -> None:
    # Revert columns added by this revision.
    op.execute("ALTER TABLE payments DROP COLUMN IF EXISTS card_no;")
    op.execute("ALTER TABLE payments DROP COLUMN IF EXISTS card_holder_name;")
    op.execute("ALTER TABLE payments DROP COLUMN IF EXISTS payment_method;")
    op.execute("ALTER TABLE payments DROP COLUMN IF EXISTS payhere_order_id;")

    # Restore old precision.
    op.execute("ALTER TABLE payments ALTER COLUMN amount TYPE NUMERIC(10, 2);")

    # NOTE:
    # PostgreSQL enum values cannot be safely removed in a generic downgrade.
