"""Expand audit event types for CD-62

Revision ID: cd62_expand_audit
Revises: cd53_add_file_integrity
Create Date: 2026-03-09 11:10:00.000000
"""

from alembic import op


revision = "cd62_expand_audit"
down_revision = "cd53_add_file_integrity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    values = [
        "USER_SUSPENDED",
        "USER_ACTIVATED",
        "KYC_AUTO_EXTRACTION_FAILED",
        "KYC_MANUAL_REVIEW_QUEUED",
        "GAZETTE_UPLOADED",
        "GAZETTE_APPROVED",
        "GAZETTE_REJECTED",
        "TAX_RULES_ACTIVATED",
        "TAX_RULES_DEACTIVATED",
        "REFUND_ISSUED",
        "LOGIN",
        "LOGOUT",
        "PASSWORD_CHANGED",
    ]
    for value in values:
        op.execute(f"ALTER TYPE auditeventtype ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    pass
