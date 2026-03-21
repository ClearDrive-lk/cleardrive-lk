"""
Vehicle database models.
Author: Parindra Chameekara
Epic: CD-E3 - Vehicle Management System
Story: CD-120 - Static Vehicle Dataset
"""

import json
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import cast

from app.core.database import Base
from sqlalchemy import DECIMAL, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Index, Integer, String, Text, Uuid
from sqlalchemy.orm import relationship


def _enum_or_string_value(value: object | None) -> object | None:
    if value is None:
        return None
    if isinstance(value, Enum):
        return cast(object, value.value)
    return value


class VehicleStatus(str, Enum):
    """Vehicle availability status."""

    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    SOLD = "SOLD"


class FuelType(str, Enum):
    """Vehicle fuel types."""

    GASOLINE = "Gasoline"
    PETROL = "Gasoline"
    DIESEL = "Diesel"
    HYBRID = "Gasoline/hybrid"
    ELECTRIC = "Electric"
    PLUGIN_HYBRID = "Plugin Hybrid"


class Transmission(str, Enum):
    """Vehicle transmission types."""

    AUTOMATIC = "Automatic"
    MANUAL = "Manual"
    CVT = "CVT"


class VehicleType(str, Enum):
    """Vehicle body types."""

    SEDAN = "Sedan"
    SUV = "SUV"
    HATCHBACK = "Hatchback"
    VAN_MINIVAN = "Van/minivan"
    WAGON = "Wagon"
    PICKUP = "Pickup"
    COUPE = "Coupe"
    CONVERTIBLE = "Convertible"
    BIKES = "Bikes"
    MACHINERY = "Machinery"


class Steering(str, Enum):
    """Steering position."""

    RIGHT_HAND = "Right Hand"
    LEFT_HAND = "Left Hand"


class Drive(str, Enum):
    """Drive type."""

    TWO_WD = "2WD"
    FOUR_WD = "4WD"
    AWD = "AWD"


class Vehicle(Base):
    """Vehicle model."""

    __tablename__ = "vehicles"
    __table_args__ = (
        Index("idx_make", "make"),
        Index("idx_model", "model"),
        Index("idx_year", "year"),
        Index("idx_price_jpy", "price_jpy"),
        Index("idx_status", "status"),
        Index("idx_make_model", "make", "model"),
        Index("idx_year_price", "year", "price_jpy"),
    )

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Columns that actually exist in this DB schema
    stock_no = Column(String(100), unique=True, nullable=False, index=True)
    chassis = Column(String(100), nullable=True)
    make = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    reg_year = Column(String(20), nullable=True)
    year = Column(Integer, nullable=False)
    vehicle_type: Column[VehicleType | None] = Column(SQLEnum(VehicleType), nullable=True)
    body_type = Column(String(100), nullable=True)
    grade = Column(String(100), nullable=True)
    price_jpy: Column[Decimal] = Column(DECIMAL(12, 2), nullable=False)
    mileage_km = Column(Integer, nullable=True)
    engine_cc = Column(Integer, nullable=True)
    motor_power_kw: Column[Decimal | None] = Column(DECIMAL(8, 2), nullable=True)
    engine_model = Column(String(100), nullable=True)
    fuel_type = Column(String(50), nullable=True)
    transmission = Column(String(50), nullable=True)
    steering: Column[Steering | None] = Column(SQLEnum(Steering), nullable=True)
    drive: Column[Drive | None] = Column(SQLEnum(Drive), nullable=True)
    seats = Column(Integer, nullable=True)
    doors = Column(Integer, nullable=True)
    color = Column(String(100), nullable=True)
    location = Column(String(200), nullable=True)
    dimensions = Column(Text, nullable=True)
    length_cm = Column(Integer, nullable=True)
    width_cm = Column(Integer, nullable=True)
    height_cm = Column(Integer, nullable=True)
    m3_size: Column[Decimal] = Column(DECIMAL(10, 2), nullable=True)
    options = Column(Text, nullable=True)
    other_remarks = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    vehicle_url = Column(Text, nullable=True)
    model_no = Column(String(100), nullable=True)
    gallery_images = Column(Text, nullable=True)
    status: Column[VehicleStatus] = Column(
        SQLEnum(VehicleStatus), default=VehicleStatus.AVAILABLE, nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    orders = relationship("Order", back_populates="vehicle")

    # Compatibility fields expected by API schemas
    @property
    def auction_id(self):
        return self.stock_no

    def __repr__(self):
        return f"<Vehicle {self.make} {self.model} ({self.year}) - Stock#{self.stock_no}>"

    def to_dict(self):
        status_value = self.status.value if isinstance(self.status, VehicleStatus) else self.status
        return {
            "id": str(self.id),
            "stock_no": self.stock_no,
            "chassis": self.chassis,
            "make": self.make,
            "model": self.model,
            "reg_year": self.reg_year,
            "year": self.year,
            "vehicle_type": None,
            "body_type": self.body_type,
            "grade": self.grade,
            "price_jpy": float(self.price_jpy),
            "mileage_km": self.mileage_km,
            "engine_cc": self.engine_cc,
            "motor_power_kw": (
                float(self.motor_power_kw) if self.motor_power_kw is not None else None
            ),
            "engine_model": self.engine_model,
            "fuel_type": _enum_or_string_value(self.fuel_type),
            "transmission": _enum_or_string_value(self.transmission),
            "steering": None,
            "drive": None,
            "seats": self.seats,
            "doors": self.doors,
            "color": self.color,
            "location": self.location,
            "dimensions": self.dimensions,
            "length_cm": self.length_cm,
            "width_cm": self.width_cm,
            "height_cm": self.height_cm,
            "m3_size": None,
            "options": self.options,
            "other_remarks": self.other_remarks,
            "image_url": self.image_url,
            "gallery_images": json.loads(self.gallery_images) if self.gallery_images else [],
            "vehicle_url": self.vehicle_url,
            "model_no": self.model_no,
            "status": status_value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
