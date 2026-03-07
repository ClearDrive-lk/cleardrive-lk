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

from app.core.database import Base
from sqlalchemy import DECIMAL, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Index, Integer, String, Text, Uuid
from sqlalchemy.orm import relationship


def _enum_or_string_value(value: object | None) -> object | None:
    if value is None:
        return None
    if isinstance(value, Enum):
        return value.value
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
    make = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    auction_grade = Column(String(10), nullable=True)
    price_jpy: Column[Decimal] = Column(DECIMAL(12, 2), nullable=False)
    mileage_km = Column(Integer, nullable=True)
    engine_cc = Column(Integer, nullable=True)
    fuel_type = Column(String(50), nullable=True)
    transmission = Column(String(50), nullable=True)
    color = Column(String(100), nullable=True)
    image_url = Column(Text, nullable=True)
    gallery_images = Column(Text, nullable=True)
    status: Column[VehicleStatus] = Column(SQLEnum(VehicleStatus), default=VehicleStatus.AVAILABLE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    orders = relationship("Order", back_populates="vehicle")

    # Compatibility fields expected by API schemas
    @property
    def auction_id(self):
        return self.stock_no

    @property
    def chassis(self):
        return None

    @property
    def reg_year(self):
        return None

    @property
    def vehicle_type(self):
        return None

    @property
    def body_type(self):
        return None

    @property
    def grade(self):
        return self.auction_grade

    @property
    def engine_model(self):
        return None

    @property
    def steering(self):
        return None

    @property
    def drive(self):
        return None

    @property
    def seats(self):
        return None

    @property
    def doors(self):
        return None

    @property
    def location(self):
        return None

    @property
    def dimensions(self):
        return None

    @property
    def length_cm(self):
        return None

    @property
    def width_cm(self):
        return None

    @property
    def height_cm(self):
        return None

    @property
    def m3_size(self):
        return None

    @property
    def options(self):
        return None

    @property
    def other_remarks(self):
        return None

    @property
    def vehicle_url(self):
        return None

    @property
    def model_no(self):
        return None

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
