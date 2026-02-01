"""add shipping_documents metadata fields

Revision ID: 252ec3f7b73d
Revises: 1e80cfeb6e0a
Create Date: 2026-01-29 23:12:02.965061

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '252ec3f7b73d'
down_revision: Union[str, None] = '1e80cfeb6e0a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add document metadata columns
    op.add_column("shipping_documents", sa.Column("document_type", sa.String(length=50), nullable=False))
    op.add_column("shipping_documents", sa.Column("file_url", sa.String(length=500), nullable=False))
    op.add_column("shipping_documents", sa.Column("file_name", sa.String(length=255), nullable=False))
    op.add_column("shipping_documents", sa.Column("file_size", sa.Integer(), nullable=True))
    op.add_column("shipping_documents", sa.Column("mime_type", sa.String(length=100), nullable=True))
    op.add_column("shipping_documents", sa.Column("sha256", sa.String(length=64), nullable=False))

    # Upload info
    op.add_column("shipping_documents", sa.Column("uploaded_by", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False))
    op.add_column("shipping_documents", sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))

    # Admin verification info
    op.add_column("shipping_documents", sa.Column("verified", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.add_column("shipping_documents", sa.Column("verified_by", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("shipping_documents", sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))

    # FK constraints (users table)
    op.create_foreign_key(
        "fk_shipping_documents_uploaded_by_users",
        "shipping_documents",
        "users",
        ["uploaded_by"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_shipping_documents_verified_by_users",
        "shipping_documents",
        "users",
        ["verified_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # Indexes
    op.create_index("ix_shipping_documents_document_type", "shipping_documents", ["document_type"])
    op.create_index("ix_shipping_documents_sha256", "shipping_documents", ["sha256"])


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_shipping_documents_sha256", table_name="shipping_documents")
    op.drop_index("ix_shipping_documents_document_type", table_name="shipping_documents")

    # Drop FKs
    op.drop_constraint("fk_shipping_documents_verified_by_users", "shipping_documents", type_="foreignkey")
    op.drop_constraint("fk_shipping_documents_uploaded_by_users", "shipping_documents", type_="foreignkey")

    # Drop columns (reverse order)
    op.drop_column("shipping_documents", "verified_at")
    op.drop_column("shipping_documents", "verified_by")
    op.drop_column("shipping_documents", "verified")
    op.drop_column("shipping_documents", "uploaded_at")
    op.drop_column("shipping_documents", "uploaded_by")

    op.drop_column("shipping_documents", "sha256")
    op.drop_column("shipping_documents", "mime_type")
    op.drop_column("shipping_documents", "file_size")
    op.drop_column("shipping_documents", "file_name")
    op.drop_column("shipping_documents", "file_url")
    op.drop_column("shipping_documents", "document_type")

