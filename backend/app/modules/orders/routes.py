# backend/app/modules/orders/routes.py

"""
Order API endpoints.
Author: Tharin
Epic: CD-E4
Stories: CD-30, CD-31, CD-32
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional
from decimal import Decimal
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_permission
from app.core.permissions import Permission
from app.modules.orders.models import Order, OrderStatus, PaymentStatus, OrderStatusHistory
from app.modules.orders.schemas import (
    OrderCreate,
    OrderResponse,
    OrderListResponse,
    OrderTimelineResponse,
    OrderStatusUpdate
)
from app.modules.auth.models import User
from app.modules.vehicles.models import Vehicle
from app.modules.kyc.models import KYCDocument, KYCStatus

router = APIRouter(prefix="/orders", tags=["orders"])


# ===================================================================
# HELPER FUNCTION: CALCULATE ORDER COSTS
# ===================================================================

def calculate_order_costs(vehicle_price_jpy: Decimal) -> dict:
    """
    Calculate total landed cost in LKR.
    
    Same formula as Parindra's vehicle cost calculator.
    """
    
    JPY_TO_LKR = Decimal("1.85")
    SHIPPING_COST_JPY = Decimal("150000")
    CUSTOMS_DUTY_RATE = Decimal("0.25")  # 25%
    VAT_RATE = Decimal("0.15")  # 15%
    
    vehicle_cost_lkr = vehicle_price_jpy * JPY_TO_LKR
    shipping_cost_lkr = SHIPPING_COST_JPY * JPY_TO_LKR
    
    cif_value = vehicle_cost_lkr + shipping_cost_lkr
    customs_duty = cif_value * CUSTOMS_DUTY_RATE
    vat = (cif_value + customs_duty) * VAT_RATE
    
    total_cost = cif_value + customs_duty + vat
    
    return {
        "vehicle_cost_lkr": vehicle_cost_lkr,
        "shipping_cost_lkr": shipping_cost_lkr,
        "customs_duty_lkr": customs_duty,
        "vat_lkr": vat,
        "total_cost_lkr": total_cost
    }


# ===================================================================
# ENDPOINT: CREATE ORDER
# ===================================================================

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new vehicle import order.
    
    **Prerequisites:**
    - User must be authenticated
    - User must have KYC APPROVED
    - Vehicle must be AVAILABLE
    
    **Process:**
    1. Verify KYC status
    2. Verify vehicle availability
    3. Calculate costs
    4. Create order record
    5. Create status history entry
    6. Return order details
    
    **Returns:**
    - Created order with all details
    - Status: CREATED
    - Payment Status: PENDING
    """
    
    print(f"\n{'='*70}")
    print(f"📝 ORDER CREATION - User: {current_user.email}")
    print(f"{'='*70}\n")
    
    # ===============================================================
    # STEP 1: VERIFY KYC STATUS
    # ===============================================================
    kyc = db.query(KYCDocument).filter(
        KYCDocument.user_id == current_user.id
    ).first()
    
    if not kyc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="KYC verification required. Please submit your documents first."
        )
    
    if kyc.status != KYCStatus.APPROVED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"KYC status is {kyc.status}. Only APPROVED users can create orders."
        )
    
    print(f"✅ KYC verified: {kyc.status}")
    
    # ===============================================================
    # STEP 2: VERIFY VEHICLE AVAILABILITY
    # ===============================================================
    vehicle = db.query(Vehicle).filter(Vehicle.id == order_data.vehicle_id).first()
    
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle {order_data.vehicle_id} not found"
        )
    
    if vehicle.status != "AVAILABLE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vehicle is {vehicle.status}, not available for order"
        )
    
    print(f"✅ Vehicle available: {vehicle.make} {vehicle.model} ({vehicle.year})")
    
    # ===============================================================
    # STEP 3: CALCULATE COSTS
    # ===============================================================
    costs = calculate_order_costs(vehicle.price_jpy)
    
    print(f"💰 Cost breakdown:")
    print(f"   Vehicle:  LKR {costs['vehicle_cost_lkr']:,.2f}")
    print(f"   Shipping: LKR {costs['shipping_cost_lkr']:,.2f}")
    print(f"   Customs:  LKR {costs['customs_duty_lkr']:,.2f}")
    print(f"   VAT:      LKR {costs['vat_lkr']:,.2f}")
    print(f"   TOTAL:    LKR {costs['total_cost_lkr']:,.2f}")
    
    # ===============================================================
    # STEP 4: CREATE ORDER
    # ===============================================================
    order = Order(
        user_id=current_user.id,
        vehicle_id=vehicle.id,
        status=OrderStatus.CREATED,
        payment_status=PaymentStatus.PENDING,
        shipping_address=order_data.shipping_address,  # TODO: Encrypt
        phone=order_data.phone,
        vehicle_cost_lkr=costs['vehicle_cost_lkr'],
        shipping_cost_lkr=costs['shipping_cost_lkr'],
        customs_duty_lkr=costs['customs_duty_lkr'],
        vat_lkr=costs['vat_lkr'],
        total_cost_lkr=costs['total_cost_lkr']
    )
    
    db.add(order)
    db.flush()  # Get order.id without committing
    
    # ===============================================================
    # STEP 5: CREATE STATUS HISTORY ENTRY
    # ===============================================================
    history = OrderStatusHistory(
        order_id=order.id,
        old_status=None,
        new_status=OrderStatus.CREATED.value,
        changed_by=current_user.id,
        notes="Order created"
    )
    
    db.add(history)
    
    # ===============================================================
    # STEP 6: MARK VEHICLE AS RESERVED
    # ===============================================================
    vehicle.status = "RESERVED"
    
    # Commit all changes
    db.commit()
    db.refresh(order)
    
    print(f"\n✅ Order created: {order.id}")
    print(f"   Status: {order.status}")
    print(f"   Payment: {order.payment_status}")
    print(f"{'='*70}\n")
    
    # TODO: Send email confirmation
    
    return order


# ===================================================================
# ENDPOINT: LIST ORDERS
# ===================================================================

@router.get("/", response_model=OrderListResponse)
async def list_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List orders.
    
    **Role-based filtering:**
    - CUSTOMER: Only their own orders
    - ADMIN: All orders
    - EXPORTER: Orders assigned to them
    - CLEARING_AGENT: Orders assigned to them
    
    **Query Parameters:**
    - page: Page number
    - limit: Items per page
    - status_filter: Filter by order status
    """
    
    # Base query
    if current_user.role == "ADMIN":
        # Admin sees all orders
        query = db.query(Order)
    else:
        # Customers see only their orders
        query = db.query(Order).filter(Order.user_id == current_user.id)
    
    # Apply status filter
    if status_filter:
        query = query.filter(Order.status == status_filter)
    
    # Sort by created date (newest first)
    query = query.order_by(Order.created_at.desc())
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * limit
    orders = query.offset(offset).limit(limit).all()
    
    total_pages = (total + limit - 1) // limit if total > 0 else 0
    
    return {
        "orders": orders,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": total_pages
        }
    }


# ===================================================================
# ENDPOINT: GET ORDER DETAILS
# ===================================================================

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get order details.
    
    **Authorization:**
    - Order owner can view
    - Admin can view all orders
    """
    
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found"
        )
    
    # Check authorization
    if current_user.role != "ADMIN" and order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this order"
        )
    
    return order


# ===================================================================
# ENDPOINT: CANCEL ORDER
# ===================================================================

@router.patch("/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel an order.
    
    **Rules:**
    - Only order owner can cancel
    - Can only cancel before SHIPPED status
    - Refund initiated if payment already made
    """
    
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found"
        )
    
    # Check ownership
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel your own orders"
        )
    
    # Check if cancellable
    non_cancellable_statuses = [
        OrderStatus.SHIPPED,
        OrderStatus.IN_TRANSIT,
        OrderStatus.ARRIVED_AT_PORT,
        OrderStatus.CUSTOMS_CLEARANCE,
        OrderStatus.DELIVERED,
        OrderStatus.CANCELLED
    ]
    
    if order.status in non_cancellable_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order in {order.status} status"
        )
    
    # Update order status
    old_status = order.status
    order.status = OrderStatus.CANCELLED
    
    # Create history entry
    history = OrderStatusHistory(
        order_id=order.id,
        old_status=old_status.value,
        new_status=OrderStatus.CANCELLED.value,
        changed_by=current_user.id,
        notes="Order cancelled by customer"
    )
    db.add(history)
    
    # Release vehicle
    vehicle = db.query(Vehicle).filter(Vehicle.id == order.vehicle_id).first()
    if vehicle:
        vehicle.status = "AVAILABLE"
    
    # TODO: Initiate refund if payment was made
    
    db.commit()
    
    print(f"❌ Order cancelled: {order_id}")
    
    return {
        "message": "Order cancelled successfully",
        "order_id": str(order_id),
        "status": order.status
    }


# ===================================================================
# ENDPOINT: ORDER TIMELINE
# ===================================================================

@router.get("/{order_id}/timeline", response_model=OrderTimelineResponse)
async def get_order_timeline(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get order status history timeline.
    
    **Returns:**
    - All status changes
    - Who made each change
    - When each change occurred
    - Notes for each change
    """
    
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found"
        )
    
    # Check authorization
    if current_user.role != "ADMIN" and order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this order"
        )
    
    # Get status history
    history = db.query(OrderStatusHistory).filter(
        OrderStatusHistory.order_id == order_id
    ).order_by(OrderStatusHistory.changed_at.asc()).all()
    
    return {
        "order_id": str(order_id),
        "current_status": order.status.value,
        "timeline": [
            {
                "old_status": h.old_status,
                "new_status": h.new_status,
                "changed_by": h.changed_by,
                "changed_at": h.changed_at,
                "notes": h.notes
            }
            for h in history
        ]
    }