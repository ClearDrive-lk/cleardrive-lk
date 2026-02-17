<<<<<<< HEAD
"""
Vehicle Pydantic schemas for request/response validation.
Author: Parindra Chameekara
Epic: CD-E3 - Vehicle Management System
Story: CD-130 - Vehicle Search & Filter API
"""
=======
# backend/app/modules/vehicles/schemas.py
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

<<<<<<< HEAD
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import Drive, FuelType, Steering, Transmission, VehicleStatus, VehicleType
=======
from pydantic import BaseModel, Field, validator

from .models import FuelType, Transmission, VehicleStatus
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7

# ============================================================================
# VEHICLE SCHEMAS
# ============================================================================


<<<<<<< HEAD
def _coerce_enum_by_name(value, enum_cls):
    if value is None:
        return None
    if isinstance(value, enum_cls):
        return value
    if isinstance(value, str):
        key = value.upper()
        if key in enum_cls.__members__:
            return enum_cls[key]
        for member in enum_cls:
            if member.value.lower() == value.lower():
                return member
    return value


class VehicleBase(BaseModel):
    """Base vehicle schema with common fields."""

    stock_no: str = Field(..., min_length=1, max_length=100)
    chassis: Optional[str] = Field(None, max_length=100)
    make: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1, max_length=100)
    reg_year: Optional[int | str] = Field(None, description="Registration year (e.g., 2023/6)")
    year: int = Field(..., ge=1980, le=2027, description="Vehicle year (1980-2027)")

    vehicle_type: Optional[VehicleType] = None
    body_type: Optional[str] = Field(None, max_length=100)
    grade: Optional[str] = Field(None, max_length=100)

=======
class VehicleBase(BaseModel):
    """Base vehicle schema."""

    auction_id: str = Field(..., description="Unique auction ID")
    make: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1, max_length=100)
    year: int = Field(..., ge=1990, le=2026, description="Vehicle year (1990-2026)")
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
    price_jpy: Decimal = Field(..., gt=0, description="Price in Japanese Yen")

    mileage_km: Optional[int] = Field(None, ge=0, description="Mileage in kilometers")
    engine_cc: Optional[int] = Field(None, ge=0, description="Engine capacity in cc")
<<<<<<< HEAD
    engine_model: Optional[str] = Field(None, max_length=100)
    fuel_type: Optional[FuelType] = None
    transmission: Optional[Transmission] = None

    steering: Optional[Steering] = None
    drive: Optional[Drive] = None
    seats: Optional[int] = Field(None, ge=1, le=50)
    doors: Optional[int] = Field(None, ge=1, le=10)

    color: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=200)

    dimensions: Optional[str] = None
    length_cm: Optional[int] = Field(None, ge=0)
    width_cm: Optional[int] = Field(None, ge=0)
    height_cm: Optional[int] = Field(None, ge=0)
    m3_size: Optional[Decimal] = Field(None, ge=0)

    options: Optional[str] = None
    other_remarks: Optional[str] = None

    image_url: Optional[str] = Field(None, max_length=500)
    vehicle_url: Optional[str] = Field(None, max_length=500)

    model_no: Optional[str] = Field(None, max_length=100)

    status: VehicleStatus = VehicleStatus.AVAILABLE

    @field_validator("reg_year", mode="before")
    @classmethod
    def normalize_reg_year(cls, v):
        if isinstance(v, str):
            if len(v) > 20:
                raise ValueError("reg_year must be at most 20 characters")
            if v.isdigit():
                return int(v)
        return v

    @field_validator("fuel_type", mode="before")
    @classmethod
    def normalize_fuel_type(cls, v):
        return _coerce_enum_by_name(v, FuelType)

    @field_validator("transmission", mode="before")
    @classmethod
    def normalize_transmission(cls, v):
        return _coerce_enum_by_name(v, Transmission)


class VehicleCreate(VehicleBase):
    """Schema for creating a new vehicle (admin only)."""

    pass


class VehicleUpdate(BaseModel):
    """Schema for updating a vehicle (admin only)."""
=======
    fuel_type: Optional[FuelType] = None
    transmission: Optional[Transmission] = None
    auction_grade: Optional[str] = Field(None, max_length=10)
    color: Optional[str] = Field(None, max_length=50)
    image_url: Optional[str] = Field(None, max_length=500)
    status: VehicleStatus = VehicleStatus.AVAILABLE


class VehicleCreate(VehicleBase):
    """Vehicle creation schema."""


class VehicleUpdate(BaseModel):
    """Vehicle update schema."""
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7

    price_jpy: Optional[Decimal] = Field(None, gt=0)
    mileage_km: Optional[int] = Field(None, ge=0)
    status: Optional[VehicleStatus] = None
    image_url: Optional[str] = None
<<<<<<< HEAD
    color: Optional[str] = None
    location: Optional[str] = None
    options: Optional[str] = None
    other_remarks: Optional[str] = None


class VehicleResponse(VehicleBase):
    """Schema for vehicle response."""
=======


class VehicleResponse(VehicleBase):
    """Vehicle response schema."""
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7

    id: UUID
    created_at: datetime
    updated_at: datetime

<<<<<<< HEAD
    model_config = ConfigDict(from_attributes=True)
=======
    class Config:
        from_attributes = True
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7


# ============================================================================
# VEHICLE SEARCH/FILTER SCHEMAS
# ============================================================================


class VehicleFilters(BaseModel):
    """Vehicle search and filter parameters."""

    # Search
    search: Optional[str] = Field(None, description="Search in make, model")

    # Filters
    make: Optional[str] = None
    model: Optional[str] = None
<<<<<<< HEAD
    vehicle_type: Optional[VehicleType] = None
    year_min: Optional[int] = Field(None, ge=1980)
    year_max: Optional[int] = Field(None, le=2027)
=======
    year_min: Optional[int] = Field(None, ge=1990)
    year_max: Optional[int] = Field(None, le=2026)
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
    price_min: Optional[Decimal] = Field(None, ge=0)
    price_max: Optional[Decimal] = None
    mileage_max: Optional[int] = Field(None, ge=0)
    fuel_type: Optional[FuelType] = None
    transmission: Optional[Transmission] = None
<<<<<<< HEAD
    drive: Optional[Drive] = None
=======
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
    status: Optional[VehicleStatus] = VehicleStatus.AVAILABLE

    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(20, ge=1, le=100, description="Items per page")

    # Sorting
    sort_by: Optional[str] = Field("created_at", description="Field to sort by")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$")

<<<<<<< HEAD
    @field_validator("sort_by")
    def validate_sort_field(cls, v):
        allowed_fields = ["price_jpy", "year", "reg_year", "mileage_km", "created_at"]
=======
    @validator("sort_by")
    def validate_sort_field(cls, v):
        allowed_fields = ["price_jpy", "year", "mileage_km", "created_at"]
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
        if v not in allowed_fields:
            raise ValueError(f"Invalid sort field. Allowed: {allowed_fields}")
        return v


<<<<<<< HEAD
class PaginationInfo(BaseModel):
    """Pagination metadata for list responses."""

    page: int = Field(..., ge=1)
    limit: int = Field(..., ge=1, le=100)
    total: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=0)


class VehicleListResponse(BaseModel):
    """Response schema for vehicle list with pagination."""

    vehicles: list[VehicleResponse]
    pagination: PaginationInfo
=======
class VehicleListResponse(BaseModel):
    """Paginated vehicle list response."""

    vehicles: list[VehicleResponse]
    total: int
    page: int
    limit: int
    total_pages: int
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7


# ============================================================================
# COST CALCULATOR SCHEMAS
# ============================================================================


class CostBreakdown(BaseModel):
    """Detailed cost breakdown for vehicle import."""

    # Base costs
    vehicle_price_jpy: Decimal
    vehicle_price_lkr: Decimal
    exchange_rate: Decimal = Field(..., description="JPY to LKR exchange rate")

    # Import costs
    shipping_cost_lkr: Decimal = Field(..., description="Estimated shipping cost")
    customs_duty_lkr: Decimal = Field(..., description="Customs duty (based on engine CC)")
    excise_duty_lkr: Decimal = Field(..., description="Excise duty")
    vat_lkr: Decimal = Field(..., description="Value Added Tax (15%)")
    cess_lkr: Decimal = Field(..., description="Cess (if applicable)")
    port_charges_lkr: Decimal = Field(..., description="Port and handling charges")

    # Service fees
    clearance_fee_lkr: Decimal = Field(..., description="Customs clearance fee")
    documentation_fee_lkr: Decimal = Field(..., description="Documentation fee")

    # Total
    total_cost_lkr: Decimal = Field(..., description="Total landed cost in LKR")

    # Breakdown percentages
    vehicle_percentage: float = Field(..., description="Vehicle cost as % of total")
    taxes_percentage: float = Field(..., description="Taxes as % of total")
    fees_percentage: float = Field(..., description="Fees as % of total")


class CostCalculatorRequest(BaseModel):
    """Cost calculator request."""

    vehicle_id: UUID
    exchange_rate: Optional[Decimal] = Field(None, description="Custom exchange rate (optional)")


<<<<<<< HEAD
class CostBreakdownResponse(BaseModel):
    """Response schema for cost calculation."""

    vehicle_id: str
    vehicle_price_jpy: float
    vehicle_price_lkr: float
    shipping_cost_lkr: float
    cif_value_lkr: float
    customs_duty_lkr: float
    vat_lkr: float
    total_cost_lkr: float
    breakdown_percentage: dict

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "vehicle_id": "123e4567-e89b-12d3-a456-426614174000",
                "vehicle_price_jpy": 2500000.0,
                "vehicle_price_lkr": 4625000.0,
                "shipping_cost_lkr": 277500.0,
                "cif_value_lkr": 4902500.0,
                "customs_duty_lkr": 1225625.0,
                "vat_lkr": 919218.75,
                "total_cost_lkr": 7047343.75,
                "breakdown_percentage": {
                    "vehicle": "65.6%",
                    "shipping": "3.9%",
                    "customs": "17.4%",
                    "vat": "13.0%",
                },
            }
        }
    )


=======
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
# ============================================================================
# POPULAR VEHICLES SCHEMAS
# ============================================================================


class PopularVehicle(BaseModel):
    """Popular vehicle statistics."""

    vehicle: VehicleResponse
    view_count: int
    order_count: int


class PopularVehiclesResponse(BaseModel):
    """Popular vehicles response."""

    vehicles: list[PopularVehicle]
    period: str = "last_30_days"
