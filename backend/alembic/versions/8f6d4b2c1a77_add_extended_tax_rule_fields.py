"""add extended tax rule fields

Revision ID: 8f6d4b2c1a77
Revises: f4e3c2b1a098
Create Date: 2026-03-20 07:15:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "8f6d4b2c1a77"
down_revision = "f4e3c2b1a098"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tax_rules", sa.Column("hs_code", sa.String(length=20), nullable=True))
    op.add_column(
        "tax_rules",
        sa.Column(
            "surcharge_percent",
            sa.Numeric(precision=5, scale=2),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "tax_rules",
        sa.Column("luxury_tax_threshold", sa.Numeric(precision=14, scale=2), nullable=True),
    )
    op.add_column(
        "tax_rules",
        sa.Column("luxury_tax_percent", sa.Numeric(precision=5, scale=2), nullable=True),
    )

    op.create_check_constraint(
        "ck_tax_rules_valid_luxury_tax_threshold",
        "tax_rules",
        "luxury_tax_threshold IS NULL OR luxury_tax_threshold >= 0",
    )
    op.create_check_constraint(
        "ck_tax_rules_valid_luxury_tax_percent",
        "tax_rules",
        "luxury_tax_percent IS NULL OR (luxury_tax_percent >= 0 AND luxury_tax_percent <= 999)",
    )

    op.drop_constraint("ck_tax_rules_valid_percentages", "tax_rules", type_="check")
    op.create_check_constraint(
        "ck_tax_rules_valid_percentages",
        "tax_rules",
        "customs_percent >= 0 AND customs_percent <= 999 "
        "AND surcharge_percent >= 0 AND surcharge_percent <= 999 "
        "AND excise_percent >= 0 AND excise_percent <= 999 "
        "AND vat_percent >= 0 AND vat_percent <= 100 "
        "AND pal_percent >= 0 AND pal_percent <= 100 "
        "AND cess_percent >= 0 AND cess_percent <= 999",
    )

    op.alter_column("tax_rules", "surcharge_percent", server_default=None)


def downgrade() -> None:
    op.drop_constraint("ck_tax_rules_valid_luxury_tax_percent", "tax_rules", type_="check")
    op.drop_constraint("ck_tax_rules_valid_luxury_tax_threshold", "tax_rules", type_="check")

    op.drop_constraint("ck_tax_rules_valid_percentages", "tax_rules", type_="check")
    op.create_check_constraint(
        "ck_tax_rules_valid_percentages",
        "tax_rules",
        "customs_percent >= 0 AND customs_percent <= 999 "
        "AND excise_percent >= 0 AND excise_percent <= 999 "
        "AND vat_percent >= 0 AND vat_percent <= 100 "
        "AND pal_percent >= 0 AND pal_percent <= 100 "
        "AND cess_percent >= 0 AND cess_percent <= 999",
    )

    op.drop_column("tax_rules", "luxury_tax_percent")
    op.drop_column("tax_rules", "luxury_tax_threshold")
    op.drop_column("tax_rules", "surcharge_percent")
    op.drop_column("tax_rules", "hs_code")
