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


class CessType(str, enum.Enum):
    """CESS calculation type."""

    PERCENT = "PERCENT"
    FIXED = "FIXED"


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
    vehicle_tax_rules: Mapped[list["VehicleTaxRule"]] = relationship(
        "VehicleTaxRule", back_populates="gazette", cascade="all, delete-orphan"
    )
    customs_rules: Mapped[list["CustomsRule"]] = relationship(
        "CustomsRule", back_populates="gazette", cascade="all, delete-orphan"
    )
    surcharge_rules: Mapped[list["SurchargeRule"]] = relationship(
        "SurchargeRule", back_populates="gazette", cascade="all, delete-orphan"
    )
    luxury_tax_rules: Mapped[list["LuxuryTaxRule"]] = relationship(
        "LuxuryTaxRule", back_populates="gazette", cascade="all, delete-orphan"
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
            "(power_kw_min IS NULL AND power_kw_max IS NULL) "
            "OR (power_kw_min IS NOT NULL AND power_kw_max IS NOT NULL AND power_kw_min <= power_kw_max)",
            name="ck_tax_rules_valid_power_range",
        ),
        CheckConstraint(
            "(age_years_min IS NULL AND age_years_max IS NULL) "
            "OR (age_years_min IS NOT NULL AND age_years_max IS NOT NULL AND age_years_min <= age_years_max)",
            name="ck_tax_rules_valid_age_range",
        ),
        CheckConstraint(
            "customs_percent >= 0 AND customs_percent <= 999 "
            "AND surcharge_percent >= 0 AND surcharge_percent <= 999 "
            "AND excise_percent >= 0 AND excise_percent <= 999 "
            "AND vat_percent >= 0 AND vat_percent <= 100 "
            "AND pal_percent >= 0 AND pal_percent <= 100 "
            "AND cess_percent >= 0 AND cess_percent <= 999",
            name="ck_tax_rules_valid_percentages",
        ),
        CheckConstraint(
            "excise_per_kw_amount IS NULL OR excise_per_kw_amount >= 0",
            name="ck_tax_rules_valid_excise_per_kw_amount",
        ),
        CheckConstraint(
            "luxury_tax_threshold IS NULL OR luxury_tax_threshold >= 0",
            name="ck_tax_rules_valid_luxury_tax_threshold",
        ),
        CheckConstraint(
            "luxury_tax_percent IS NULL OR (luxury_tax_percent >= 0 AND luxury_tax_percent <= 999)",
            name="ck_tax_rules_valid_luxury_tax_percent",
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
    category_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    hs_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    engine_min: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    engine_max: Mapped[int] = mapped_column(Integer, nullable=False, default=999999)
    power_kw_min: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    power_kw_max: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    age_years_min: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    age_years_max: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    customs_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    surcharge_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    excise_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    excise_per_kw_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    vat_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=15.00)
    pal_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=7.50)
    cess_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    luxury_tax_threshold: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    luxury_tax_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
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


class VehicleTaxRule(Base):
    """Vehicle-rule table for matching excise rules and HS codes."""

    __tablename__ = "vehicle_tax_rules"
    __table_args__ = (
        CheckConstraint(
            "fuel_type IN ('PETROL', 'DIESEL', 'ELECTRIC', 'HYBRID', 'OTHER')",
            name="ck_vehicle_tax_rules_valid_fuel_type",
        ),
        CheckConstraint(
            "power_kw_min <= power_kw_max", name="ck_vehicle_tax_rules_valid_power_range"
        ),
        CheckConstraint(
            "age_years_min <= age_years_max",
            name="ck_vehicle_tax_rules_valid_age_range",
        ),
        CheckConstraint(
            "excise_type IN ('PER_KW', 'PERCENTAGE')",
            name="ck_vehicle_tax_rules_valid_excise_type",
        ),
        Index("idx_vehicle_tax_rules_gazette_id", "gazette_id"),
        Index(
            "idx_vehicle_tax_rules_lookup",
            "category_code",
            "fuel_type",
            "power_kw_min",
            "power_kw_max",
            "age_years_min",
            "age_years_max",
            "is_active",
            postgresql_where=text("is_active = true"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    gazette_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("gazettes.id", ondelete="CASCADE"), nullable=False
    )
    category_code: Mapped[str] = mapped_column(String(100), nullable=False)
    fuel_type: Mapped[str] = mapped_column(String(50), nullable=False)
    hs_code: Mapped[str] = mapped_column(String(20), nullable=False)
    power_kw_min: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    power_kw_max: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    age_years_min: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    age_years_max: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    excise_type: Mapped[str] = mapped_column(String(20), nullable=False, default="PER_KW")
    excise_rate: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
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

    gazette = relationship("Gazette", back_populates="vehicle_tax_rules")
    approver = relationship("User", foreign_keys=[approved_by_admin])


class CustomsRule(Base):
    """Lookup table for customs/VAT/PAL/CESS by HS code."""

    __tablename__ = "customs_rules"
    __table_args__ = (
        CheckConstraint(
            "cess_type IN ('PERCENT', 'FIXED')",
            name="ck_customs_rules_valid_cess_type",
        ),
        Index("idx_customs_rules_gazette_id", "gazette_id"),
        Index(
            "idx_customs_rules_lookup",
            "hs_code",
            "is_active",
            postgresql_where=text("is_active = true"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    gazette_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("gazettes.id", ondelete="CASCADE"), nullable=False
    )
    hs_code: Mapped[str] = mapped_column(String(20), nullable=False)
    customs_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    vat_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    pal_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    cess_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default=CessType.PERCENT.value
    )
    cess_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
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

    gazette = relationship("Gazette", back_populates="customs_rules")
    approver = relationship("User", foreign_keys=[approved_by_admin])


class SurchargeRule(Base):
    """Global customs surcharge rules."""

    __tablename__ = "surcharge_rules"
    __table_args__ = (
        Index("idx_surcharge_rules_gazette_id", "gazette_id"),
        Index(
            "idx_surcharge_rules_lookup",
            "applies_to",
            "is_active",
            postgresql_where=text("is_active = true"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    gazette_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("gazettes.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, default="CUSTOMS_SURCHARGE")
    rate_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    applies_to: Mapped[str] = mapped_column(String(50), nullable=False, default="CUSTOMS_DUTY")
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

    gazette = relationship("Gazette", back_populates="surcharge_rules")
    approver = relationship("User", foreign_keys=[approved_by_admin])


class LuxuryTaxRule(Base):
    """Lookup table for luxury tax thresholds by HS code."""

    __tablename__ = "luxury_tax_rules"
    __table_args__ = (
        Index("idx_luxury_tax_rules_gazette_id", "gazette_id"),
        Index(
            "idx_luxury_tax_rules_lookup",
            "hs_code",
            "is_active",
            postgresql_where=text("is_active = true"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    gazette_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("gazettes.id", ondelete="CASCADE"), nullable=False
    )
    hs_code: Mapped[str] = mapped_column(String(20), nullable=False)
    threshold_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    rate_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
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

    gazette = relationship("Gazette", back_populates="luxury_tax_rules")
    approver = relationship("User", foreign_keys=[approved_by_admin])
