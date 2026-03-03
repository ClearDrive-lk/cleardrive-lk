"""Add tax_rules table for vehicle import tax calculations.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-03 16:06:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tax_rules",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("gazette_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vehicle_type", sa.String(length=50), nullable=False),
        sa.Column("fuel_type", sa.String(length=50), nullable=False),
        sa.Column("engine_min", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("engine_max", sa.Integer(), nullable=False, server_default="999999"),
        sa.Column("customs_percent", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0"),
        sa.Column("excise_percent", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0"),
        sa.Column("vat_percent", sa.Numeric(precision=5, scale=2), nullable=False, server_default="15.00"),
        sa.Column("pal_percent", sa.Numeric(precision=5, scale=2), nullable=False, server_default="7.50"),
        sa.Column("cess_percent", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0"),
        sa.Column("apply_on", sa.String(length=30), nullable=False, server_default="CIF"),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("approved_by_admin", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["gazette_id"], ["gazettes.id"], name="fk_tax_rules_gazette_id", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["approved_by_admin"], ["users.id"], name="fk_tax_rules_approved_by", ondelete="SET NULL"
        ),
        sa.CheckConstraint(
            "vehicle_type IN ('SEDAN', 'SUV', 'TRUCK', 'VAN', 'MOTORCYCLE', 'ELECTRIC', 'BUS', 'OTHER')",
            name="ck_tax_rules_valid_vehicle_type",
        ),
        sa.CheckConstraint(
            "fuel_type IN ('PETROL', 'DIESEL', 'ELECTRIC', 'HYBRID', 'OTHER')",
            name="ck_tax_rules_valid_fuel_type",
        ),
        sa.CheckConstraint(
            "apply_on IN ('CIF', 'CIF_PLUS_CUSTOMS', 'CUSTOMS_ONLY', 'CIF_PLUS_EXCISE')",
            name="ck_tax_rules_valid_apply_on",
        ),
        sa.CheckConstraint("engine_min <= engine_max", name="ck_tax_rules_valid_engine_range"),
        sa.CheckConstraint(
            "customs_percent >= 0 AND customs_percent <= 999 AND "
            "excise_percent >= 0 AND excise_percent <= 999 AND "
            "vat_percent >= 0 AND vat_percent <= 100 AND "
            "pal_percent >= 0 AND pal_percent <= 100 AND "
            "cess_percent >= 0 AND cess_percent <= 999",
            name="ck_tax_rules_valid_percentages",
        ),
    )

    op.create_index(
        "idx_tax_rules_lookup",
        "tax_rules",
        ["vehicle_type", "fuel_type", "engine_min", "engine_max", "is_active"],
        postgresql_where=sa.text("is_active = true"),
    )
    op.create_index("idx_tax_rules_gazette_id", "tax_rules", ["gazette_id"])
    op.execute("CREATE INDEX idx_tax_rules_effective_date ON tax_rules (effective_date DESC);")
    op.create_index(
        "idx_tax_rules_is_active",
        "tax_rules",
        ["is_active"],
        postgresql_where=sa.text("is_active = true"),
    )


def downgrade() -> None:
    op.drop_index("idx_tax_rules_is_active", table_name="tax_rules")
    op.drop_index("idx_tax_rules_effective_date", table_name="tax_rules")
    op.drop_index("idx_tax_rules_gazette_id", table_name="tax_rules")
    op.drop_index("idx_tax_rules_lookup", table_name="tax_rules")
    op.drop_table("tax_rules")
