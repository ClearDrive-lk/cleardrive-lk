"""Add gazettes table for gazette PDF management.

Revision ID: a1b2c3d4e5f6
Revises: d6f8b2a1c9e4
Create Date: 2026-03-03 16:05:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "d6f8b2a1c9e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "gazettes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("gazette_no", sa.String(length=50), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("raw_extracted", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("gazette_no", name="uq_gazettes_gazette_no"),
        sa.ForeignKeyConstraint(
            ["uploaded_by"], ["users.id"], name="fk_gazettes_uploaded_by", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["approved_by"], ["users.id"], name="fk_gazettes_approved_by", ondelete="SET NULL"
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'REJECTED')", name="ck_gazettes_valid_status"
        ),
    )

    op.create_index("idx_gazettes_status", "gazettes", ["status"])
    op.create_index("idx_gazettes_effective_date", "gazettes", ["effective_date"])
    op.execute("CREATE INDEX idx_gazettes_created_at ON gazettes (created_at DESC);")


def downgrade() -> None:
    op.drop_index("idx_gazettes_created_at", table_name="gazettes")
    op.drop_index("idx_gazettes_effective_date", table_name="gazettes")
    op.drop_index("idx_gazettes_status", table_name="gazettes")
    op.drop_table("gazettes")
