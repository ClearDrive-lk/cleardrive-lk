"""Expand audit events for CD-92 tiered rate limiting.

Revision ID: cd92_expand_audit
Revises: cd62_expand_audit
Create Date: 2026-03-09 12:10:00.000000
"""

from alembic import op


revision = "cd92_expand_audit"
down_revision = "cd62_expand_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    values = [
        "USER_TIER_DOWNGRADED",
        "USER_TIER_UPGRADED",
    ]
    for value in values:
        op.execute(f"ALTER TYPE auditeventtype ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    pass
