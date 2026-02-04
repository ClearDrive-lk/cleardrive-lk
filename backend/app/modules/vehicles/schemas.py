# backend/app/modules/vehicles/schemas.py

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

from .models import FuelType, Transmission, VehicleStatus

# ============================================================================
# VEHICLE SCHEMAS
# ============================================================================


class VehicleBase(BaseModel):
    """Base vehicle schema."""

    auction_id: str = Field(..., description="Unique auction ID")
    make: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1, max_length=100)
    year: int = Field(..., ge=1990, le=2026, description="Vehicle year (1990-2026)")
    price_jpy: Decimal = Field(..., gt=0, description="Price in Japanese Yen")

    mileage_km: Optional[int] = Field(None, ge=0, description="Mileage in kilometers")
    engine_cc: Optional[int] = Field(None, ge=0, description="Engine capacity in cc")
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

    price_jpy: Optional[Decimal] = Field(None, gt=0)
    mileage_km: Optional[int] = Field(None, ge=0)
    status: Optional[VehicleStatus] = None
    image_url: Optional[str] = None


class VehicleResponse(VehicleBase):
    """Vehicle response schema."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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
    year_min: Optional[int] = Field(None, ge=1990)
    year_max: Optional[int] = Field(None, le=2026)
    price_min: Optional[Decimal] = Field(None, ge=0)
    price_max: Optional[Decimal] = None
    mileage_max: Optional[int] = Field(None, ge=0)
    fuel_type: Optional[FuelType] = None
    transmission: Optional[Transmission] = None
    status: Optional[VehicleStatus] = VehicleStatus.AVAILABLE

    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(20, ge=1, le=100, description="Items per page")

    # Sorting
    sort_by: Optional[str] = Field("created_at", description="Field to sort by")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$")

    @validator("sort_by")
    def validate_sort_field(cls, v):
        allowed_fields = ["price_jpy", "year", "mileage_km", "created_at"]
        if v not in allowed_fields:
            raise ValueError(f"Invalid sort field. Allowed: {allowed_fields}")
        return v


class VehicleListResponse(BaseModel):
    """Paginated vehicle list response."""

    vehicles: list[VehicleResponse]
    total: int
    page: int
    limit: int
    total_pages: int


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
