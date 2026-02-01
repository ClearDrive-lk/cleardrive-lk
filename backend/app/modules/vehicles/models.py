# backend/app/modules/vehicles/models.py

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.core.database import Base
from app.core.models import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.modules.orders.models import Order


class VehicleStatus(str, enum.Enum):
    """Vehicle availability status."""

    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    SOLD = "SOLD"
    UNAVAILABLE = "UNAVAILABLE"


class FuelType(str, enum.Enum):
    """Fuel type enum."""

    PETROL = "PETROL"
    DIESEL = "DIESEL"
    HYBRID = "HYBRID"
    ELECTRIC = "ELECTRIC"
    CNG = "CNG"


class Transmission(str, enum.Enum):
    """Transmission type enum."""

    MANUAL = "MANUAL"
    AUTOMATIC = "AUTOMATIC"
    CVT = "CVT"
    SEMI_AUTOMATIC = "SEMI_AUTOMATIC"


class Vehicle(Base, UUIDMixin, TimestampMixin):
    """Vehicle model - imported vehicles."""

    __tablename__ = "vehicles"

    # Auction info
    auction_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )

    # Vehicle details
    make: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Pricing
    price_jpy: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Specifications
    mileage_km: Mapped[int | None] = mapped_column(Integer)
    engine_cc: Mapped[int | None] = mapped_column(Integer)
    fuel_type: Mapped[FuelType | None] = mapped_column(SQLEnum(FuelType))
    transmission: Mapped[Transmission | None] = mapped_column(SQLEnum(Transmission))

    # Condition
    auction_grade: Mapped[str | None] = mapped_column(
        String(10)
    )  # e.g., "4.5", "5", "R"
    color: Mapped[str | None] = mapped_column(String(50))

    # Media
    image_url: Mapped[str | None] = mapped_column(String(500))

    # Status
    status: Mapped[VehicleStatus] = mapped_column(
        SQLEnum(VehicleStatus),
        default=VehicleStatus.AVAILABLE,
        nullable=False,
        index=True,
    )

    # Relationships
    orders: Mapped[list[Order]] = relationship("Order", back_populates="vehicle")

    def __repr__(self):
        return f"<Vehicle {self.make} {self.model} ({self.year})>"
