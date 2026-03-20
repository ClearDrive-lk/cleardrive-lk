"""add dedicated tax rule tables

Revision ID: 5d2a7c9e3f11
Revises: 8f6d4b2c1a77
Create Date: 2026-03-20 08:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "5d2a7c9e3f11"
down_revision = "8f6d4b2c1a77"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vehicle_tax_rules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("gazette_id", sa.UUID(), nullable=False),
        sa.Column("category_code", sa.String(length=100), nullable=False),
        sa.Column("fuel_type", sa.String(length=50), nullable=False),
        sa.Column("hs_code", sa.String(length=20), nullable=False),
        sa.Column("power_kw_min", sa.Numeric(8, 2), nullable=False),
        sa.Column("power_kw_max", sa.Numeric(8, 2), nullable=False),
        sa.Column("age_years_min", sa.Numeric(5, 2), nullable=False),
        sa.Column("age_years_max", sa.Numeric(5, 2), nullable=False),
        sa.Column("excise_type", sa.String(length=20), nullable=False),
        sa.Column("excise_rate", sa.Numeric(12, 2), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("approved_by_admin", sa.UUID(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=False),
        sa.ForeignKeyConstraint(["approved_by_admin"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["gazette_id"], ["gazettes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("power_kw_min <= power_kw_max", name="ck_vehicle_tax_rules_valid_power_range"),
        sa.CheckConstraint("age_years_min <= age_years_max", name="ck_vehicle_tax_rules_valid_age_range"),
        sa.CheckConstraint("excise_type IN ('PER_KW', 'PERCENTAGE')", name="ck_vehicle_tax_rules_valid_excise_type"),
    )
    op.create_index("idx_vehicle_tax_rules_gazette_id", "vehicle_tax_rules", ["gazette_id"])
    op.create_index(
        "idx_vehicle_tax_rules_lookup",
        "vehicle_tax_rules",
        ["category_code", "fuel_type", "power_kw_min", "power_kw_max", "age_years_min", "age_years_max", "is_active"],
    )

    op.create_table(
        "customs_rules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("gazette_id", sa.UUID(), nullable=False),
        sa.Column("hs_code", sa.String(length=20), nullable=False),
        sa.Column("customs_percent", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("vat_percent", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("pal_percent", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("cess_type", sa.String(length=20), nullable=False, server_default="PERCENT"),
        sa.Column("cess_value", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("approved_by_admin", sa.UUID(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=False),
        sa.ForeignKeyConstraint(["approved_by_admin"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["gazette_id"], ["gazettes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("cess_type IN ('PERCENT', 'FIXED')", name="ck_customs_rules_valid_cess_type"),
    )
    op.create_index("idx_customs_rules_gazette_id", "customs_rules", ["gazette_id"])
    op.create_index("idx_customs_rules_lookup", "customs_rules", ["hs_code", "is_active"])

    op.create_table(
        "surcharge_rules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("gazette_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("rate_percent", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("applies_to", sa.String(length=50), nullable=False, server_default="CUSTOMS_DUTY"),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("approved_by_admin", sa.UUID(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=False),
        sa.ForeignKeyConstraint(["approved_by_admin"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["gazette_id"], ["gazettes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_surcharge_rules_gazette_id", "surcharge_rules", ["gazette_id"])
    op.create_index("idx_surcharge_rules_lookup", "surcharge_rules", ["applies_to", "is_active"])

    op.create_table(
        "luxury_tax_rules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("gazette_id", sa.UUID(), nullable=False),
        sa.Column("hs_code", sa.String(length=20), nullable=False),
        sa.Column("threshold_value", sa.Numeric(14, 2), nullable=False),
        sa.Column("rate_percent", sa.Numeric(5, 2), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("approved_by_admin", sa.UUID(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=False),
        sa.ForeignKeyConstraint(["approved_by_admin"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["gazette_id"], ["gazettes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_luxury_tax_rules_gazette_id", "luxury_tax_rules", ["gazette_id"])
    op.create_index("idx_luxury_tax_rules_lookup", "luxury_tax_rules", ["hs_code", "is_active"])


def downgrade() -> None:
    op.drop_index("idx_luxury_tax_rules_lookup", table_name="luxury_tax_rules")
    op.drop_index("idx_luxury_tax_rules_gazette_id", table_name="luxury_tax_rules")
    op.drop_table("luxury_tax_rules")

    op.drop_index("idx_surcharge_rules_lookup", table_name="surcharge_rules")
    op.drop_index("idx_surcharge_rules_gazette_id", table_name="surcharge_rules")
    op.drop_table("surcharge_rules")

    op.drop_index("idx_customs_rules_lookup", table_name="customs_rules")
    op.drop_index("idx_customs_rules_gazette_id", table_name="customs_rules")
    op.drop_table("customs_rules")

    op.drop_index("idx_vehicle_tax_rules_lookup", table_name="vehicle_tax_rules")
    op.drop_index("idx_vehicle_tax_rules_gazette_id", table_name="vehicle_tax_rules")
    op.drop_table("vehicle_tax_rules")
