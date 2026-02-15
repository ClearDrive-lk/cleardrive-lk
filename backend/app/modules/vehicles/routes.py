"""
Vehicle Pydantic schemas for request/response validation.
Author: Parindra Chameekara
Epic: CD-E3 - Vehicle Management System
Story: CD-140 - Vehicle detail and cost calculation endpoints
"""

import math
from decimal import Decimal
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.modules.vehicles.models import Vehicle, VehicleStatus
from app.modules.vehicles.schemas import (
    CostBreakdown,
    PaginationInfo,
    VehicleCreate,
    VehicleListResponse,
    VehicleResponse,
    VehicleUpdate,
)
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Session

# Import cost calculator if it exists
try:
    from .cost_calculator import DEFAULT_JPY_TO_LKR, calculate_total_cost

    HAS_COST_CALCULATOR = True
except ImportError:
    HAS_COST_CALCULATOR = False
    # Fallback constants
    DEFAULT_JPY_TO_LKR = Decimal("1.85")
    SHIPPING_COST_JPY = Decimal("150000")
    CUSTOMS_DUTY_RATE = Decimal("0.25")
    VAT_RATE = Decimal("0.15")

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


# ============================================================================
# PUBLIC ENDPOINTS (No auth required)
# ============================================================================


@router.get("", response_model=VehicleListResponse)
async def get_vehicles(
    # Search & Filter Parameters
    search: Optional[str] = Query(None, description="Search in make/model"),
    make: Optional[str] = Query(None, description="Filter by manufacturer"),
    model: Optional[str] = Query(None, description="Filter by model"),
    year_min: Optional[int] = Query(None, ge=1990, description="Minimum year"),
    year_max: Optional[int] = Query(None, le=2026, description="Maximum year"),
    price_min: Optional[Decimal] = Query(None, ge=0, description="Minimum price (JPY)"),
    price_max: Optional[Decimal] = Query(None, ge=0, description="Maximum price (JPY)"),
    mileage_max: Optional[int] = Query(None, ge=0, description="Maximum mileage (km)"),
    fuel_type: Optional[str] = Query(None, description="Filter by fuel type"),
    transmission: Optional[str] = Query(None, description="Filter by transmission"),
    status: VehicleStatus = Query(VehicleStatus.AVAILABLE, description="Filter by status"),
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    # Sorting
    sort_by: str = Query(
        "created_at",
        pattern="^(price_jpy|year|reg_year|mileage_km|created_at)$",
        description="Field to sort by",
    ),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    # Database session
    db: Session = Depends(get_db),
):
    """
    Get paginated list of vehicles with filters and sorting.

    **Query Parameters:**
    - `search`: Search text for make/model
    - `make`: Filter by manufacturer (e.g., "Toyota")
    - `model`: Filter by model (e.g., "Prius")
    - `year_min`, `year_max`: Year range filter
    - `price_min`, `price_max`: Price range in JPY
    - `mileage_max`: Maximum mileage filter
    - `fuel_type`: Filter by fuel type
    - `transmission`: Filter by transmission type
    - `status`: Filter by status (default: AVAILABLE)
    - `page`: Page number (default: 1)
    - `limit`: Results per page (default: 20, max: 100)
    - `sort_by`: Field to sort by (price_jpy, year, reg_year, mileage_km, created_at)
    - `sort_order`: Sort order (asc or desc)

    **Returns:**
    - List of vehicles matching filters
    - Pagination information

    Public endpoint - no authentication required.
    """

    # Build query
    query = db.query(Vehicle)

    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Vehicle.make.ilike(search_term),
                Vehicle.model.ilike(search_term),
            )
        )

    if make:
        query = query.filter(Vehicle.make.ilike(f"%{make}%"))

    if model:
        query = query.filter(Vehicle.model.ilike(f"%{model}%"))

    if year_min:
        query = query.filter(Vehicle.year >= year_min)

    if year_max:
        query = query.filter(Vehicle.year <= year_max)

    if price_min:
        query = query.filter(Vehicle.price_jpy >= price_min)

    if price_max:
        query = query.filter(Vehicle.price_jpy <= price_max)

    if mileage_max:
        query = query.filter(Vehicle.mileage_km <= mileage_max)

    if fuel_type:
        query = query.filter(Vehicle.fuel_type == fuel_type)

    if transmission:
        query = query.filter(Vehicle.transmission == transmission)

    if status:
        query = query.filter(Vehicle.status == status)

    # Get total count before pagination
    total = query.count()

    # Apply sorting
    sort_column = getattr(Vehicle, sort_by)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    # Apply pagination
    offset = (page - 1) * limit
    vehicles = query.offset(offset).limit(limit).all()

    # Calculate total pages
    total_pages = math.ceil(total / limit) if total > 0 else 0

    return VehicleListResponse(
        vehicles=[VehicleResponse.model_validate(v) for v in vehicles],
        pagination=PaginationInfo(page=page, limit=limit, total=total, total_pages=total_pages),
    )


@router.get("/makes/list")
async def list_makes(db: Session = Depends(get_db)):
    """
    Get list of all unique vehicle makes (manufacturers).

    **Returns:**
    - List of unique manufacturers

    **Usage:**
    - For dropdown filters in frontend

    Public endpoint - no authentication required.
    """

    makes = db.query(Vehicle.make).distinct().order_by(Vehicle.make).all()
    return {"makes": [make[0] for make in makes]}


@router.get("/models/list")
async def list_models(
    make: Optional[str] = Query(None, description="Filter models by manufacturer"),
    db: Session = Depends(get_db),
):
    """
    Get list of models, optionally filtered by make.

    **Query Parameters:**
    - `make`: Filter models by manufacturer

    **Returns:**
    - List of unique models

    **Usage:**
    - For dropdown filters in frontend

    Public endpoint - no authentication required.
    """

    query = db.query(Vehicle.model).distinct()

    if make:
        query = query.filter(Vehicle.make == make)

    models = query.order_by(Vehicle.model).all()
    return {"models": [model[0] for model in models]}


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific vehicle.

    **Path Parameters:**
    - `vehicle_id`: UUID of the vehicle

    **Returns:**
    - Complete vehicle details

    **Errors:**
    - 404: Vehicle not found

    Public endpoint - no authentication required.
    """

    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Vehicle with ID {vehicle_id} not found"
        )

    return VehicleResponse.model_validate(vehicle)


@router.get("/{vehicle_id}/cost", response_model=CostBreakdown)
async def calculate_cost(
    vehicle_id: UUID,
    exchange_rate: Optional[Decimal] = Query(None, description="Custom JPY to LKR rate"),
    db: Session = Depends(get_db),
):
    """
    Calculate total import cost for a vehicle.

    **Cost Breakdown:**
    1. Vehicle price (JPY → LKR conversion)
    2. Shipping cost
    3. CIF value (Cost + Insurance + Freight)
    4. Customs duty (25% of CIF)
    5. VAT (15% of CIF + Customs)
    6. Total cost in LKR

    **Path Parameters:**
    - `vehicle_id`: UUID of the vehicle

    **Query Parameters:**
    - `exchange_rate`: Optional custom JPY to LKR exchange rate

    **Returns:**
    - Detailed cost breakdown with percentages

    **Errors:**
    - 404: Vehicle not found

    Public endpoint - no authentication required.
    """

    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Vehicle with ID {vehicle_id} not found"
        )

    # Use custom exchange rate or default
    rate = exchange_rate or DEFAULT_JPY_TO_LKR

    # Calculate cost using dedicated calculator if available
    if HAS_COST_CALCULATOR:
        try:
            cost_data = calculate_total_cost(vehicle, rate)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    else:
        # Fallback calculation
        vehicle_cost_lkr = Decimal(str(vehicle.price_jpy)) * rate
        shipping_cost_lkr = SHIPPING_COST_JPY * rate

        # CIF = Cost + Insurance + Freight
        cif_value = vehicle_cost_lkr + shipping_cost_lkr

        # Customs duty = 25% of CIF
        customs_duty = cif_value * CUSTOMS_DUTY_RATE

        # VAT = 15% of (CIF + Duty)
        vat = (cif_value + customs_duty) * VAT_RATE

        # Total cost
        total_cost = cif_value + customs_duty + vat

        # Calculate percentages
        def calc_percentage(amount: Decimal, total: Decimal) -> Decimal:
            if total == 0:
                return Decimal("0.0")
            return ((amount / total) * 100).quantize(Decimal("0.1"))

        cost_data = {
            "vehicle_price_jpy": vehicle.price_jpy,
            "vehicle_price_lkr": vehicle_cost_lkr,
            "exchange_rate": rate,
            "shipping_cost_lkr": shipping_cost_lkr,
            "customs_duty_lkr": customs_duty,
            "excise_duty_lkr": Decimal("0"),
            "vat_lkr": vat,
            "cess_lkr": Decimal("0"),
            "port_charges_lkr": Decimal("0"),
            "clearance_fee_lkr": Decimal("0"),
            "documentation_fee_lkr": Decimal("0"),
            "total_cost_lkr": total_cost,
            "vehicle_percentage": calc_percentage(vehicle_cost_lkr, total_cost),
            "taxes_percentage": calc_percentage(customs_duty + vat, total_cost),
            "fees_percentage": calc_percentage(shipping_cost_lkr, total_cost),
        }

    # Pass Decimals directly; Pydantic handles coercion
    return CostBreakdown(**cost_data)  # type: ignore[arg-type]


# ============================================================================
# ADMIN ENDPOINTS (Requires ADMIN role)
# ============================================================================


@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    vehicle_data: VehicleCreate,
    current_user=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Create a new vehicle.

    **Request Body:**
    - Vehicle data (see VehicleCreate schema)

    **Returns:**
    - Created vehicle details

    **Errors:**
    - 400: Vehicle with auction_id already exists

    Requires ADMIN role.
    """

    # Check if stock_no already exists
    existing = db.query(Vehicle).filter(Vehicle.stock_no == vehicle_data.stock_no).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vehicle with stock_no '{vehicle_data.stock_no}' already exists",
        )

    # Create vehicle
    vehicle = Vehicle(**vehicle_data.model_dump())

    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    return VehicleResponse.model_validate(vehicle)


@router.patch("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: UUID,
    vehicle_data: VehicleUpdate,
    current_user=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Update a vehicle.

    **Path Parameters:**
    - `vehicle_id`: UUID of the vehicle

    **Request Body:**
    - Fields to update (see VehicleUpdate schema)

    **Returns:**
    - Updated vehicle details

    **Errors:**
    - 404: Vehicle not found

    Requires ADMIN role.
    """

    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    # Update fields
    update_data = vehicle_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(vehicle, field, value)

    db.commit()
    db.refresh(vehicle)

    return VehicleResponse.model_validate(vehicle)


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(
    vehicle_id: UUID,
    current_user=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Delete a vehicle.

    **Path Parameters:**
    - `vehicle_id`: UUID of the vehicle

    **Returns:**
    - No content (204)

    **Errors:**
    - 404: Vehicle not found
    - 400: Cannot delete vehicle with existing orders

    Requires ADMIN role.
    """

    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    # Check if vehicle has orders
    # TODO: Add this check when Order model is imported
    # if vehicle.orders:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Cannot delete vehicle with existing orders"
    #     )

    db.delete(vehicle)
    db.commit()

    return None
