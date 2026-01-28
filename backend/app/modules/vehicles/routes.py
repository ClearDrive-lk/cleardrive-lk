# backend/app/modules/vehicles/routes.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, asc
from typing import Optional
from uuid import UUID
from decimal import Decimal
import math

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_current_admin
from app.core.permissions import Permission, require_permission

from .models import Vehicle, VehicleStatus
from .schemas import (
    VehicleResponse,
    VehicleCreate,
    VehicleUpdate,
    VehicleFilters,
    VehicleListResponse,
    CostBreakdown,
    CostCalculatorRequest,
)
from .cost_calculator import calculate_total_cost, DEFAULT_JPY_TO_LKR

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


# ============================================================================
# PUBLIC ENDPOINTS (No auth required)
# ============================================================================

@router.get("", response_model=VehicleListResponse)
async def get_vehicles(
    search: Optional[str] = None,
    make: Optional[str] = None,
    model: Optional[str] = None,
    year_min: Optional[int] = Query(None, ge=1990),
    year_max: Optional[int] = Query(None, le=2026),
    price_min: Optional[Decimal] = Query(None, ge=0),
    price_max: Optional[Decimal] = None,
    mileage_max: Optional[int] = Query(None, ge=0),
    fuel_type: Optional[str] = None,
    transmission: Optional[str] = None,
    status: VehicleStatus = VehicleStatus.AVAILABLE,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", regex="^(price_jpy|year|mileage_km|created_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    """
    Get paginated list of vehicles with filters.
    
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
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get vehicle by ID.
    
    Public endpoint - no authentication required.
    """
    
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
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
    
    Public endpoint - no authentication required.
    """
    
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    
    # Use custom exchange rate or default
    rate = exchange_rate or DEFAULT_JPY_TO_LKR
    
    # Calculate cost
    cost_data = calculate_total_cost(vehicle, rate)
    
    return CostBreakdown(**cost_data)


# ============================================================================
# ADMIN ENDPOINTS (Requires ADMIN role)
# ============================================================================

@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    vehicle_data: VehicleCreate,
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Create a new vehicle.
    
    Requires ADMIN role.
    """
    
    # Check if auction_id already exists
    existing = db.query(Vehicle).filter(Vehicle.auction_id == vehicle_data.auction_id).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vehicle with auction_id '{vehicle_data.auction_id}' already exists"
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
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Update a vehicle.
    
    Requires ADMIN role.
    """
    
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    
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
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Delete a vehicle.
    
    Requires ADMIN role.
    """
    
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    
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