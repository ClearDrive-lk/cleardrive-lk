"""add audit_logs table

Revision ID: 611ce2705ddc
Revises: 3247b739293f
Create Date: 2026-02-22 07:20:40.606208

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "611ce2705ddc"
down_revision: Union[str, None] = "3247b739293f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum(
                "ROLE_CHANGED",
                "USER_CREATED",
                "USER_DELETED",
                "KYC_APPROVED",
                "KYC_REJECTED",
                "ORDER_STATUS_CHANGED",
                "PAYMENT_PROCESSED",
                name="auditeventtype",
            ),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("admin_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_admin_id"), "audit_logs", ["admin_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_created_at"), "audit_logs", ["created_at"], unique=False)
    op.create_index(op.f("ix_audit_logs_event_type"), "audit_logs", ["event_type"], unique=False)
    op.create_index(op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_logs_user_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_event_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_created_at"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_admin_id"), table_name="audit_logs")
    op.drop_table("audit_logs")
