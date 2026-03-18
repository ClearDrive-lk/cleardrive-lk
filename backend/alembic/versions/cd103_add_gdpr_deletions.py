"""Add GDPR deletions table and audit events for CD-103

Revision ID: cd103_add_gdpr_deletions
Revises: cd92_expand_audit
Create Date: 2026-03-18 11:25:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "cd103_add_gdpr_deletions"
down_revision: Union[str, None] = "cd92_expand_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE auditeventtype ADD VALUE IF NOT EXISTS 'GDPR_DELETION_REQUESTED'")
    op.execute("ALTER TYPE auditeventtype ADD VALUE IF NOT EXISTS 'GDPR_DELETION_COMPLETED'")
    op.execute("ALTER TYPE auditeventtype ADD VALUE IF NOT EXISTS 'GDPR_DELETION_REJECTED'")

    gdpr_status_enum = sa.Enum(
        "REQUESTED",
        "PROCESSING",
        "COMPLETED",
        "REJECTED",
        name="gdprdeletionstatus",
    )
    gdpr_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "gdpr_deletions",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", gdpr_status_enum, nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("data_anonymized", sa.Boolean(), nullable=False),
        sa.Column("kyc_deleted", sa.Boolean(), nullable=False),
        sa.Column("sessions_revoked", sa.Boolean(), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("original_email", sa.String(length=255), nullable=True),
        sa.Column("original_name", sa.String(length=255), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_gdpr_deletions_status"), "gdpr_deletions", ["status"], unique=False)
    op.create_index(op.f("ix_gdpr_deletions_user_id"), "gdpr_deletions", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_gdpr_deletions_user_id"), table_name="gdpr_deletions")
    op.drop_index(op.f("ix_gdpr_deletions_status"), table_name="gdpr_deletions")
    op.drop_table("gdpr_deletions")
