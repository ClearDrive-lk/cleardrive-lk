# backend/app/modules/vehicles/models.py

from sqlalchemy import Column, String, Integer, Numeric, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base
from app.core.models import TimestampMixin, UUIDMixin


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
    auction_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Vehicle details
    make = Column(String(100), nullable=False, index=True)
    model = Column(String(100), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    
    # Pricing
    price_jpy = Column(Numeric(10, 2), nullable=False)
    
    # Specifications
    mileage_km = Column(Integer)
    engine_cc = Column(Integer)
    fuel_type = Column(SQLEnum(FuelType))
    transmission = Column(SQLEnum(Transmission))
    
    # Condition
    auction_grade = Column(String(10))  # e.g., "4.5", "5", "R"
    color = Column(String(50))
    
    # Media
    image_url = Column(String(500))
    
    # Status
    status = Column(SQLEnum(VehicleStatus), default=VehicleStatus.AVAILABLE, nullable=False, index=True)
    
    # Relationships
    orders = relationship("Order", back_populates="vehicle")
    
    def __repr__(self):
        return f"<Vehicle {self.make} {self.model} ({self.year})>"