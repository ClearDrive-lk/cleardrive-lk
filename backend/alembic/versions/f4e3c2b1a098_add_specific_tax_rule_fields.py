"""Add specific tax-rule fields for electric and age-based gazettes.

Revision ID: f4e3c2b1a098
Revises: cccb8e5e9fd0
Create Date: 2026-03-19 23:45:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f4e3c2b1a098"
down_revision: Union[str, None] = "cccb8e5e9fd0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tax_rules", sa.Column("category_code", sa.String(length=100), nullable=True))
    op.add_column("tax_rules", sa.Column("power_kw_min", sa.Numeric(precision=8, scale=2), nullable=True))
    op.add_column("tax_rules", sa.Column("power_kw_max", sa.Numeric(precision=8, scale=2), nullable=True))
    op.add_column("tax_rules", sa.Column("age_years_min", sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column("tax_rules", sa.Column("age_years_max", sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column(
        "tax_rules",
        sa.Column("excise_per_kw_amount", sa.Numeric(precision=12, scale=2), nullable=True),
    )
    op.add_column("vehicles", sa.Column("motor_power_kw", sa.Numeric(precision=8, scale=2), nullable=True))

    op.create_check_constraint(
        "ck_tax_rules_valid_power_range",
        "tax_rules",
        "(power_kw_min IS NULL AND power_kw_max IS NULL) "
        "OR (power_kw_min IS NOT NULL AND power_kw_max IS NOT NULL AND power_kw_min <= power_kw_max)",
    )
    op.create_check_constraint(
        "ck_tax_rules_valid_age_range",
        "tax_rules",
        "(age_years_min IS NULL AND age_years_max IS NULL) "
        "OR (age_years_min IS NOT NULL AND age_years_max IS NOT NULL AND age_years_min <= age_years_max)",
    )
    op.create_check_constraint(
        "ck_tax_rules_valid_excise_per_kw_amount",
        "tax_rules",
        "excise_per_kw_amount IS NULL OR excise_per_kw_amount >= 0",
    )


def downgrade() -> None:
    op.drop_constraint("ck_tax_rules_valid_excise_per_kw_amount", "tax_rules", type_="check")
    op.drop_constraint("ck_tax_rules_valid_age_range", "tax_rules", type_="check")
    op.drop_constraint("ck_tax_rules_valid_power_range", "tax_rules", type_="check")

    op.drop_column("vehicles", "motor_power_kw")
    op.drop_column("tax_rules", "excise_per_kw_amount")
    op.drop_column("tax_rules", "age_years_max")
    op.drop_column("tax_rules", "age_years_min")
    op.drop_column("tax_rules", "power_kw_max")
    op.drop_column("tax_rules", "power_kw_min")
    op.drop_column("tax_rules", "category_code")
