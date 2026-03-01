"""
Vehicle database models.
Author: Parindra Chameekara
Epic: CD-E3 - Vehicle Management System
Story: CD-120 - Static Vehicle Dataset
"""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum

from app.core.database import Base
from sqlalchemy import DECIMAL, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Integer, String, Text, Uuid
from sqlalchemy.orm import relationship


class VehicleStatus(str, Enum):
    """Vehicle availability status."""

    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    SOLD = "SOLD"


class FuelType(str, Enum):
    """Vehicle fuel types."""

    GASOLINE = "Gasoline"
    # Backward compatibility for existing DB enum rows using PETROL.
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
    """
    Vehicle model representing Japanese auction vehicles from ramadbk.com.

    This table stores all vehicle listings available for import.
    Data can be:
    1. Static (from JSON file)
    2. Scraped (from Japanese auction sites like ramadbk.com)
    """

    __tablename__ = "vehicles"

    # Primary Key
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Stock and Auction Information
    stock_no = Column(String(100), unique=True, nullable=False, index=True)  # Stock No. from CSV
    chassis = Column(String(100), nullable=True)  # Chassis number (masked as ****)

    # Basic Vehicle Information
    make = Column(String(100), nullable=False, index=True)
    model = Column(String(100), nullable=False, index=True)
    reg_year = Column(String(20), nullable=True)  # Registration year (e.g., "2023/6")
    year = Column(Integer, nullable=False, index=True)  # Extracted year for filtering

    # Vehicle Classification
    vehicle_type: Column[VehicleType] = Column(SQLEnum(VehicleType), nullable=True)  # Type from CSV
    body_type = Column(String(100), nullable=True)  # Body Type from CSV
    grade = Column(String(100), nullable=True)  # Grade from CSV

    # Pricing
    price_jpy: Column[Decimal] = Column(DECIMAL(12, 2), nullable=False)

    # Specifications
    mileage_km = Column(Integer, nullable=True)
    engine_cc = Column(Integer, nullable=True)
    engine_model = Column(String(100), nullable=True)  # Engine Model from CSV
    fuel_type: Column[FuelType] = Column(SQLEnum(FuelType, omit_aliases=False), nullable=True)
    transmission: Column[Transmission] = Column(SQLEnum(Transmission), nullable=True)

    # Additional Specifications
    steering: Column[Steering] = Column(SQLEnum(Steering), nullable=True)  # Steering position
    drive: Column[Drive] = Column(SQLEnum(Drive), nullable=True)  # Drive type (2WD/4WD)
    seats = Column(Integer, nullable=True)  # Number of seats
    doors = Column(Integer, nullable=True)  # Number of doors

    # Vehicle Details
    color = Column(String(100), nullable=True)  # Colour from CSV
    location = Column(String(200), nullable=True)  # Location (e.g., "Japan » Yokohama")

    # Dimensions
    dimensions = Column(Text, nullable=True)  # Full dimensions string from CSV
    length_cm = Column(Integer, nullable=True)  # Length in cm
    width_cm = Column(Integer, nullable=True)  # Width in cm
    height_cm = Column(Integer, nullable=True)  # Height in cm
    m3_size: Column[Decimal] = Column(DECIMAL(10, 2), nullable=True)  # M3 Size

    # Features and Options
    options = Column(Text, nullable=True)  # Options from CSV (comma-separated)
    other_remarks = Column(Text, nullable=True)  # Other Remarks from CSV

    # Media and Links
    image_url = Column(Text, nullable=True)  # Primary image URL
    vehicle_url = Column(Text, nullable=True)  # URL to vehicle listing

    # Additional Model Information
    model_no = Column(String(100), nullable=True)  # Model No from CSV

    # Status
    status: Column[VehicleStatus] = Column(
        SQLEnum(VehicleStatus), default=VehicleStatus.AVAILABLE, nullable=False, index=True
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships (will be used by other modules)
    orders = relationship("Order", back_populates="vehicle")

    @property
    def auction_id(self):
        """Provide 'auction_id' for compatibility with Pydantic schemas."""
        return self.stock_no

    def __repr__(self):
        return f"<Vehicle {self.make} {self.model} ({self.year}) - Stock#{self.stock_no}>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "stock_no": self.stock_no,
            "chassis": self.chassis,
            "make": self.make,
            "model": self.model,
            "reg_year": self.reg_year,
            "year": self.year,
            "vehicle_type": self.vehicle_type.value if self.vehicle_type else None,
            "body_type": self.body_type,
            "grade": self.grade,
            "price_jpy": float(self.price_jpy),
            "mileage_km": self.mileage_km,
            "engine_cc": self.engine_cc,
            "engine_model": self.engine_model,
            "fuel_type": self.fuel_type.value if self.fuel_type else None,
            "transmission": self.transmission.value if self.transmission else None,
            "steering": self.steering.value if self.steering else None,
            "drive": self.drive.value if self.drive else None,
            "seats": self.seats,
            "doors": self.doors,
            "color": self.color,
            "location": self.location,
            "dimensions": self.dimensions,
            "length_cm": self.length_cm,
            "width_cm": self.width_cm,
            "height_cm": self.height_cm,
            "m3_size": float(self.m3_size) if self.m3_size else None,
            "options": self.options,
            "other_remarks": self.other_remarks,
            "image_url": self.image_url,
            "vehicle_url": self.vehicle_url,
            "model_no": self.model_no,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
