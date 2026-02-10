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
from app.modules.orders.schemas import (
    CD30OrderCreate,
    InspectionData,
    OrderCreate,
    OrderResponse,
)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("")
@require_permission_decorator(Permission.CREATE_ORDER)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Create a new order.
    Requires: CREATE_ORDER permission
    """
    # Permission already checked by decorator
    # ... create order logic
    pass


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


@router.post("/cd30", response_model=OrderResponse, status_code=201)
async def create_cd30_order(
    order_data: CD30OrderCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new CD30 order with vehicle inspection data.
    
    Story: CD-30
    """
    # Verify vehicle exists
    vehicle = db.query(Vehicle).filter(Vehicle.id == order_data.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Calculate costs (you'll need your cost calculation logic)
    # ... cost calculation ...
    
    # Create order with inspection data
    new_order = Order(
        user_id=current_user.id,
        vehicle_id=order_data.vehicle_id,
        shipping_address=order_data.shipping_address,
        phone=order_data.phone,
        # Add inspection fields
        inspection_status=order_data.inspection_data.status,
        inspector_notes=order_data.inspection_data.notes,
        inspection_images=json.dumps(order_data.inspection_data.images),
        inspection_date=order_data.inspection_data.date,
        inspector_id=current_user.id,
        # ... add cost fields ...
    )
    
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    
    return new_order