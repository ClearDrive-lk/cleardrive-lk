"""
Gazette and tax rule models.
Stories: CD-2.7, CD-2.8
"""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from app.core.database import Base
from app.core.models import GUID
from sqlalchemy import (
    JSON,
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    desc,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship


class GazetteStatus(str, enum.Enum):
    """Gazette workflow status."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class TaxVehicleType(str, enum.Enum):
    """Vehicle type groups for tax rules."""

    SEDAN = "SEDAN"
    SUV = "SUV"
    TRUCK = "TRUCK"
    VAN = "VAN"
    MOTORCYCLE = "MOTORCYCLE"
    ELECTRIC = "ELECTRIC"
    BUS = "BUS"
    OTHER = "OTHER"


class TaxFuelType(str, enum.Enum):
    """Fuel type groups for tax rules."""

    PETROL = "PETROL"
    DIESEL = "DIESEL"
    ELECTRIC = "ELECTRIC"
    HYBRID = "HYBRID"
    OTHER = "OTHER"


class ApplyOn(str, enum.Enum):
    """Tax base type."""

    CIF = "CIF"
    CIF_PLUS_CUSTOMS = "CIF_PLUS_CUSTOMS"
    CUSTOMS_ONLY = "CUSTOMS_ONLY"
    CIF_PLUS_EXCISE = "CIF_PLUS_EXCISE"


class Gazette(Base):
    """Uploaded gazette documents and extracted payload."""

    __tablename__ = "gazettes"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'REJECTED')",
            name="ck_gazettes_valid_status",
        ),
        Index("idx_gazettes_status", "status"),
        Index("idx_gazettes_effective_date", "effective_date"),
        Index("idx_gazettes_created_at", desc("created_at")),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    gazette_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Use generic JSON at ORM layer for sqlite test compatibility.
    raw_extracted: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=GazetteStatus.PENDING.value
    )
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    uploader = relationship("User", foreign_keys=[uploaded_by])
    approver = relationship("User", foreign_keys=[approved_by])
    tax_rules: Mapped[list["TaxRule"]] = relationship(
        "TaxRule", back_populates="gazette", cascade="all, delete-orphan"
    )


class TaxRule(Base):
    """Tax rules extracted from approved gazettes."""

    __tablename__ = "tax_rules"
    __table_args__ = (
        CheckConstraint(
            "vehicle_type IN ('SEDAN', 'SUV', 'TRUCK', 'VAN', 'MOTORCYCLE', 'ELECTRIC', 'BUS', 'OTHER')",
            name="ck_tax_rules_valid_vehicle_type",
        ),
        CheckConstraint(
            "fuel_type IN ('PETROL', 'DIESEL', 'ELECTRIC', 'HYBRID', 'OTHER')",
            name="ck_tax_rules_valid_fuel_type",
        ),
        CheckConstraint(
            "apply_on IN ('CIF', 'CIF_PLUS_CUSTOMS', 'CUSTOMS_ONLY', 'CIF_PLUS_EXCISE')",
            name="ck_tax_rules_valid_apply_on",
        ),
        CheckConstraint("engine_min <= engine_max", name="ck_tax_rules_valid_engine_range"),
        CheckConstraint(
            "customs_percent >= 0 AND customs_percent <= 999 "
            "AND excise_percent >= 0 AND excise_percent <= 999 "
            "AND vat_percent >= 0 AND vat_percent <= 100 "
            "AND pal_percent >= 0 AND pal_percent <= 100 "
            "AND cess_percent >= 0 AND cess_percent <= 999",
            name="ck_tax_rules_valid_percentages",
        ),
        Index("idx_tax_rules_gazette_id", "gazette_id"),
        Index("idx_tax_rules_effective_date", desc("effective_date")),
        Index(
            "idx_tax_rules_is_active",
            "is_active",
            postgresql_where=text("is_active = true"),
        ),
        Index(
            "idx_tax_rules_lookup",
            "vehicle_type",
            "fuel_type",
            "engine_min",
            "engine_max",
            "is_active",
            postgresql_where=text("is_active = true"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    gazette_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("gazettes.id", ondelete="CASCADE"), nullable=False
    )
    vehicle_type: Mapped[str] = mapped_column(String(50), nullable=False)
    fuel_type: Mapped[str] = mapped_column(String(50), nullable=False)
    engine_min: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    engine_max: Mapped[int] = mapped_column(Integer, nullable=False, default=999999)
    customs_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    excise_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    vat_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=15.00)
    pal_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=7.50)
    cess_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    apply_on: Mapped[str] = mapped_column(String(30), nullable=False, default=ApplyOn.CIF.value)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    approved_by_admin: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    gazette = relationship("Gazette", back_populates="tax_rules")
    approver = relationship("User", foreign_keys=[approved_by_admin])
