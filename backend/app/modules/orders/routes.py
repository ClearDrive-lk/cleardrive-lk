from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.permissions import Permission
from app.core.permissions import admin_only_decorator as admin_only
from app.core.permissions import (
    has_permission,
    require_permission_decorator,
    verify_resource_ownership,
)
from app.modules.auth.models import User
from app.modules.orders.models import Order

from app.modules.orders.models import Order, OrderStatus, PaymentStatus

from app.modules.orders.schemas import (
    CD30OrderCreate,
    InspectionData,
    OrderCreate,
    OrderResponse,
)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderResponse, status_code=201)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Create a new order.
    Requires: CREATE_ORDER permission
    """
    from app.modules.vehicles.models import Vehicle
    from decimal import Decimal
    
    # Manual permission check
    if not has_permission(current_user, Permission.CREATE_ORDER):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # 1. Verify vehicle exists and is available
    vehicle = db.query(Vehicle).filter(Vehicle.id == order_data.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    if vehicle.status != "AVAILABLE":
        raise HTTPException(status_code=400, detail="Vehicle is not available")
    
    # 2. Calculate total cost
    vehicle_cost_lkr = Decimal(str(vehicle.price_jpy)) * Decimal("2.80")  # Exchange rate
    shipping_cost_lkr = Decimal("500000.00")  # Fixed shipping
    customs_duty_lkr = vehicle_cost_lkr * Decimal("0.15")  # 15% duty
    vat_lkr = (vehicle_cost_lkr + shipping_cost_lkr + customs_duty_lkr) * Decimal("0.15")  # 15% VAT
    total_cost_lkr = vehicle_cost_lkr + shipping_cost_lkr + customs_duty_lkr + vat_lkr
    
    # 3. Create the order (only with fields that exist in the model)
    new_order = Order(
        user_id=current_user.id,
        vehicle_id=order_data.vehicle_id,
        shipping_address=order_data.shipping_address,
        phone=order_data.phone,
        status=OrderStatus.CREATED,
        payment_status=PaymentStatus.PENDING,
        total_cost_lkr=total_cost_lkr,  # Only this cost field exists
    )
    
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    
    # 4. Update vehicle status to RESERVED
    vehicle.status = "RESERVED"
    db.commit()
    
    return new_order


@router.get("/{order_id}")
# @require_permission(Permission.VIEW_OWN_ORDERS, Permission.VIEW_ALL_ORDERS)
@require_permission_decorator(Permission.VIEW_OWN_ORDERS, Permission.VIEW_ALL_ORDERS)
async def get_order(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get order by ID.
    Requires: VIEW_OWN_ORDERS OR VIEW_ALL_ORDERS
    """
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(404, "Order not found")

    # If user has VIEW_ALL_ORDERS, allow access
    if has_permission(current_user, Permission.VIEW_ALL_ORDERS):
        return order

    # Otherwise, verify ownership
    verify_resource_ownership(current_user, order.user_id)

    return order


@router.delete("/{order_id}")
@admin_only()
async def delete_order(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Delete order (admin only).
    """
    # Admin permission already checked
    # ... delete order logic
    pass


