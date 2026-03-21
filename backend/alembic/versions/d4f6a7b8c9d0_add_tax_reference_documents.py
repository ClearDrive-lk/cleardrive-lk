"""add tax reference documents

Revision ID: d4f6a7b8c9d0
Revises: f9a1c3e5d7b9
Create Date: 2026-03-21 12:40:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d4f6a7b8c9d0"
down_revision = "f9a1c3e5d7b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tax_reference_documents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("issued_label", sa.String(length=120), nullable=False),
        sa.Column("document_type", sa.String(length=120), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_url", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_tax_reference_documents_active",
        "tax_reference_documents",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        "idx_tax_reference_documents_display_order",
        "tax_reference_documents",
        ["display_order"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_tax_reference_documents_display_order", table_name="tax_reference_documents")
    op.drop_index("idx_tax_reference_documents_active", table_name="tax_reference_documents")
    op.drop_table("tax_reference_documents")
