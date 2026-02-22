"""Add shipment_details table

Revision ID: 11598ea177e4
Revises: a7837696f581
Create Date: 2026-02-15 07:12:59.371808
"""

import sqlalchemy as sa
from alembic import op

revision = "11598ea177e4"  # pragma: allowlist secret
down_revision = "a7837696f581"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "shipment_details",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.UUID(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("shipment_details")
