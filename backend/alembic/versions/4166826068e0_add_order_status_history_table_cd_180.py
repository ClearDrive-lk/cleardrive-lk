"""Add order status history table (CD-180).

Revision ID: 4166826068e0
Revises: cd92_expand_audit
Create Date: 2026-03-10 12:43:30.165823
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "4166826068e0"
down_revision: Union[str, None] = "cd92_expand_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "order_status_history",
        sa.Column("ip_address", sa.String(length=45), nullable=True),
    )
    op.add_column(
        "order_status_history",
        sa.Column("user_agent", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "idx_order_status_history_created_at",
        "order_status_history",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "idx_order_status_history_to_status",
        "order_status_history",
        ["to_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_order_status_history_to_status", table_name="order_status_history")
    op.drop_index("idx_order_status_history_created_at", table_name="order_status_history")
    op.drop_column("order_status_history", "user_agent")
    op.drop_column("order_status_history", "ip_address")
