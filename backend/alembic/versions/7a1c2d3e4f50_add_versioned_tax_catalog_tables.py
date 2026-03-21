"""add versioned tax catalog tables

Revision ID: 7a1c2d3e4f50
Revises: 611ce2705ddc
Create Date: 2026-03-20 12:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "7a1c2d3e4f50"
down_revision = "611ce2705ddc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("audit_logs", sa.Column("action_type", sa.String(length=20), nullable=True))
    op.add_column("audit_logs", sa.Column("table_name", sa.String(length=100), nullable=True))
    op.add_column("audit_logs", sa.Column("record_id", sa.String(length=100), nullable=True))
    op.add_column("audit_logs", sa.Column("old_value", sa.JSON(), nullable=True))
    op.add_column("audit_logs", sa.Column("new_value", sa.JSON(), nullable=True))
    op.add_column("audit_logs", sa.Column("change_reason", sa.Text(), nullable=True))
    op.add_column("audit_logs", sa.Column("version", sa.Integer(), nullable=True))
    op.create_index("ix_audit_logs_action_type", "audit_logs", ["action_type"], unique=False)
    op.create_index("ix_audit_logs_table_name", "audit_logs", ["table_name"], unique=False)
    op.create_index("ix_audit_logs_record_id", "audit_logs", ["record_id"], unique=False)

    op.create_table(
        "global_tax_parameters",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("parameter_group", sa.String(length=100), nullable=False),
        sa.Column("parameter_name", sa.String(length=100), nullable=False),
        sa.Column("condition_or_type", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Numeric(14, 2), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=False),
        sa.Column("calculation_order", sa.Integer(), nullable=False),
        sa.Column("applicability_flag", sa.String(length=100), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=False),
        sa.Column("superseded_at", sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("calculation_order >= 0", name="ck_global_tax_parameters_calc_order"),
        sa.CheckConstraint("version >= 1", name="ck_global_tax_parameters_version"),
    )
    op.create_index(
        "idx_global_tax_parameters_active_lookup",
        "global_tax_parameters",
        ["parameter_group", "parameter_name", "condition_or_type", "is_active"],
        unique=False,
    )
    op.create_index(
        "idx_global_tax_parameters_effective_date",
        "global_tax_parameters",
        ["effective_date"],
        unique=False,
    )

    op.create_table(
        "hs_code_matrix",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("vehicle_type", sa.String(length=100), nullable=False),
        sa.Column("fuel_type", sa.String(length=50), nullable=False),
        sa.Column("age_condition", sa.String(length=20), nullable=False),
        sa.Column("hs_code", sa.String(length=20), nullable=False),
        sa.Column("capacity_min", sa.Numeric(10, 2), nullable=False),
        sa.Column("capacity_max", sa.Numeric(10, 2), nullable=False),
        sa.Column("capacity_unit", sa.String(length=20), nullable=False),
        sa.Column("cid_pct", sa.Numeric(6, 2), nullable=False, server_default="0"),
        sa.Column("pal_pct", sa.Numeric(6, 2), nullable=False, server_default="0"),
        sa.Column("cess_pct", sa.Numeric(6, 2), nullable=False, server_default="0"),
        sa.Column("excise_unit_rate_lkr", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False),
        sa.Column("superseded_at", sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("capacity_min <= capacity_max", name="ck_hs_code_matrix_capacity_range"),
        sa.CheckConstraint("version >= 1", name="ck_hs_code_matrix_version"),
        sa.CheckConstraint(
            "age_condition IN ('<=1', '>1-2', '>1-3', '>2-3', '>3-5', '>5-10', '>10')",
            name="ck_hs_code_matrix_age_condition",
        ),
    )
    op.create_index(
        "idx_hs_code_matrix_active_lookup",
        "hs_code_matrix",
        ["vehicle_type", "fuel_type", "age_condition", "capacity_min", "capacity_max", "is_active"],
        unique=False,
    )
    op.create_index(
        "idx_hs_code_matrix_effective_date", "hs_code_matrix", ["effective_date"], unique=False
    )


def downgrade() -> None:
    op.drop_index("idx_hs_code_matrix_effective_date", table_name="hs_code_matrix")
    op.drop_index("idx_hs_code_matrix_active_lookup", table_name="hs_code_matrix")
    op.drop_table("hs_code_matrix")

    op.drop_index("idx_global_tax_parameters_effective_date", table_name="global_tax_parameters")
    op.drop_index("idx_global_tax_parameters_active_lookup", table_name="global_tax_parameters")
    op.drop_table("global_tax_parameters")

    op.drop_index("ix_audit_logs_record_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_table_name", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action_type", table_name="audit_logs")
    op.drop_column("audit_logs", "version")
    op.drop_column("audit_logs", "change_reason")
    op.drop_column("audit_logs", "new_value")
    op.drop_column("audit_logs", "old_value")
    op.drop_column("audit_logs", "record_id")
    op.drop_column("audit_logs", "table_name")
    op.drop_column("audit_logs", "action_type")
