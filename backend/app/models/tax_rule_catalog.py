"""
Versioned tax parameter catalog models.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from app.core.database import Base
from app.core.models import GUID
from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Date,
    Index,
    Integer,
    Numeric,
    String,
    desc,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

_ALLOWED_AGE_CONDITIONS = (
    "<=1",
    ">1-2",
    ">1-3",
    ">2-3",
    ">3-5",
    ">5-10",
    ">10",
)


class GlobalTaxParameter(Base):
    """Global tax parameters with built-in versioning and superseding."""

    __tablename__ = "global_tax_parameters"
    __table_args__ = (
        CheckConstraint("calculation_order >= 0", name="ck_global_tax_parameters_calc_order"),
        CheckConstraint("version >= 1", name="ck_global_tax_parameters_version"),
        Index("idx_global_tax_parameters_effective_date", desc("effective_date")),
        Index(
            "idx_global_tax_parameters_active_lookup",
            "parameter_group",
            "parameter_name",
            "condition_or_type",
            "is_active",
            postgresql_where=text("is_active = true"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    parameter_group: Mapped[str] = mapped_column(String(100), nullable=False)
    parameter_name: Mapped[str] = mapped_column(String(100), nullable=False)
    condition_or_type: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    calculation_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    applicability_flag: Mapped[str | None] = mapped_column(String(100), nullable=True)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    superseded_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)


class HSCodeMatrixRule(Base):
    """Versioned HS-code matrix rules for capacity/age-based lookups."""

    __tablename__ = "hs_code_matrix"
    __table_args__ = (
        CheckConstraint("capacity_min <= capacity_max", name="ck_hs_code_matrix_capacity_range"),
        CheckConstraint("version >= 1", name="ck_hs_code_matrix_version"),
        CheckConstraint(
            "age_condition IN ('<=1', '>1-2', '>1-3', '>2-3', '>3-5', '>5-10', '>10')",
            name="ck_hs_code_matrix_age_condition",
        ),
        Index("idx_hs_code_matrix_effective_date", desc("effective_date")),
        Index(
            "idx_hs_code_matrix_active_lookup",
            "vehicle_type",
            "fuel_type",
            "age_condition",
            "capacity_min",
            "capacity_max",
            "is_active",
            postgresql_where=text("is_active = true"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    vehicle_type: Mapped[str] = mapped_column(String(100), nullable=False)
    fuel_type: Mapped[str] = mapped_column(String(50), nullable=False)
    age_condition: Mapped[str] = mapped_column(String(20), nullable=False)
    hs_code: Mapped[str] = mapped_column(String(20), nullable=False)
    capacity_min: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    capacity_max: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    capacity_unit: Mapped[str] = mapped_column(String(20), nullable=False)
    cid_pct: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    pal_pct: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    cess_pct: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    excise_unit_rate_lkr: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    min_excise_flat_rate_lkr: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=0
    )
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    superseded_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)


def is_allowed_age_condition(value: str) -> bool:
    return value in _ALLOWED_AGE_CONDITIONS
