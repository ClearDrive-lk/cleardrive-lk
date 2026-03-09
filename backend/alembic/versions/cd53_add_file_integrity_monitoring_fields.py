"""Add file integrity monitoring fields for CD-53

Revision ID: cd53_add_file_integrity
Revises: 8b7c1d2e3f4a
Create Date: 2026-03-09 09:20:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "cd53_add_file_integrity"
down_revision = "8b7c1d2e3f4a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "file_integrity", sa.Column("verification_error", sa.String(length=500), nullable=True)
    )
    op.add_column(
        "file_integrity",
        sa.Column(
            "tampering_detected", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
    )
    op.add_column(
        "file_integrity",
        sa.Column("tampering_detected_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("file_integrity", "tampering_detected_at")
    op.drop_column("file_integrity", "tampering_detected")
    op.drop_column("file_integrity", "verification_error")
