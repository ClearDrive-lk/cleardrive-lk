import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_current_user
from app.core.permissions import (
    Permission,
)
from app.core.permissions import admin_only_decorator as admin_only
from app.core.permissions import (
    has_permission,
    require_permission_decorator,
    verify_resource_ownership,
)
from app.core.security import encrypt_field
from app.modules.auth.models import Role, User
from app.modules.kyc.models import KYCDocument, KYCStatus
from app.modules.notifications.service import send_status_change_notification
from app.modules.orders.models import (
    Order,
    OrderStatus,
    OrderStatusHistory,
    PaymentStatus,
)
from app.modules.orders.schemas import (
    OrderCreate,
    OrderListItem,
    OrderResponse,
    OrderStatusHistoryResponse,
    OrderTimelineResponse,
)
from app.modules.orders.state_machine import (
    get_allowed_next_states,
    validate_state_transition,
)
from app.services.email import send_email
from app.services.notification_service import notification_service
from app.services.orders.status_history import status_history_service
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, text
from sqlalchemy.orm import Session

router = APIRouter(prefix="/orders", tags=["Orders"])
logger = logging.getLogger(__name__)


def _get_vehicle_for_order(db: Session, vehicle_id: str):
    """Fetch only required vehicle fields in a DB-schema-compatible way."""
    query = text("""
        SELECT id, price_jpy, status
        FROM vehicles
        WHERE id = :vehicle_id
        """)
    return db.execute(query, {"vehicle_id": vehicle_id}).mappings().first()


def _customer_must_own_order(order: Order, current_user: User) -> bool:
    return current_user.role == Role.CUSTOMER and order.user_id != current_user.id


@router.post("", response_model=OrderResponse, status_code=201)
async def create_order(
    request: Request,
    order_data: OrderCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Create a new order.
    Requires: CREATE_ORDER permission
    """
    from decimal import Decimal

    # Manual permission check
    if not has_permission(current_user, Permission.CREATE_ORDER):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # 1. Verify KYC status (CD-30.3)
    # TEMP LOCAL BYPASS: set to False immediately after manual API testing.
    BYPASS_KYC_FOR_LOCAL_TEST = True
    if not BYPASS_KYC_FOR_LOCAL_TEST:
        kyc = db.query(KYCDocument).filter(KYCDocument.user_id == current_user.id).first()
        if not kyc:
            raise HTTPException(
                status_code=400,
                detail="KYC verification required. Please submit your documents first.",
            )

        kyc_status = kyc.status.value if hasattr(kyc.status, "value") else kyc.status
        if kyc_status != KYCStatus.APPROVED.value:
            raise HTTPException(
                status_code=400,
                detail=f"KYC status is {kyc_status}. Only APPROVED users can create orders.",
            )

    # 2. Verify vehicle exists and is available
    vehicle = _get_vehicle_for_order(db, str(order_data.vehicle_id))
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    if str(vehicle["status"]) != "AVAILABLE":
        raise HTTPException(status_code=400, detail="Vehicle is not available")

    # 3. Calculate total cost
    vehicle_cost_lkr = Decimal(str(vehicle["price_jpy"])) * Decimal("2.80")  # Exchange rate
    shipping_cost_lkr = Decimal("500000.00")  # Fixed shipping
    customs_duty_lkr = vehicle_cost_lkr * Decimal("0.15")  # 15% duty
    vat_lkr = (vehicle_cost_lkr + shipping_cost_lkr + customs_duty_lkr) * Decimal("0.15")  # 15% VAT
    total_cost_lkr = vehicle_cost_lkr + shipping_cost_lkr + customs_duty_lkr + vat_lkr

    # 4. Encrypt shipping address (CD-30.4)
    encrypted_shipping_address = encrypt_field(order_data.shipping_address)
    if not encrypted_shipping_address:
        raise HTTPException(status_code=500, detail="Failed to encrypt shipping address")

    # 5. Create the order (only with fields that exist in the model)
    new_order = Order(
        user_id=current_user.id,
        vehicle_id=order_data.vehicle_id,
        shipping_address=encrypted_shipping_address,
        phone=order_data.phone,
        status=OrderStatus.CREATED,
        payment_status=PaymentStatus.PENDING,
        total_cost_lkr=total_cost_lkr,  # Only this cost field exists
    )

    db.add(new_order)
    db.flush()

    # ===============================================================
    # CD-32.3: CREATE INITIAL STATUS HISTORY
    # ===============================================================
    status_history_service.create_history_entry(
        db=db,
        order=new_order,
        from_status=None,  # No previous status
        to_status=OrderStatus.CREATED,
        changed_by=current_user,
        notes="Order created by customer",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(new_order)

    # 6. Update vehicle status to RESERVED
    db.execute(
        text("UPDATE vehicles SET status = :status WHERE id = :vehicle_id"),
        {"status": "RESERVED", "vehicle_id": str(order_data.vehicle_id)},
    )
    db.commit()

    # 7. Send confirmation email (CD-30.7)
    vehicle_name = (
        f"{vehicle['make']} {vehicle['model']} ({vehicle['year']})"
        if "make" in vehicle
        else "Selected Vehicle"
    )
    chassis_no = vehicle.get("chassis_no", "N/A")

    email_sent_id = await notification_service.send_order_confirmation(
        email=current_user.email,
        user_name=current_user.name or "Customer",
        order_id=str(new_order.id),
        vehicle_name=vehicle_name,
        chassis_no=chassis_no,
        total_price=f"LKR {new_order.total_cost_lkr:,.2f}" if new_order.total_cost_lkr else "N/A",
    )

    if not email_sent_id:
        logger.warning(
            "Order created but confirmation email failed for user_id=%s", current_user.id
        )

    return new_order


@router.get("", response_model=list[OrderListItem])
@require_permission_decorator(Permission.VIEW_OWN_ORDERS, Permission.VIEW_ALL_ORDERS)
async def list_orders(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List orders for customer and staff dashboards."""
    query = db.query(Order)

    if current_user.role == Role.CUSTOMER:
        query = query.filter(Order.user_id == current_user.id)

    return query.order_by(Order.created_at.desc()).all()


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


# 27/02/2026

# ===================================================================
# ENDPOINT: UPDATE ORDER STATUS (CD-31.5)
# ===================================================================


@router.patch("/{order_id}/status")
async def update_order_status(
    request: Request,
    order_id: str,
    new_status: str,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update order status (state machine transition).

    **Story**: CD-31 - Order State Machine

    **Permissions:**
    - ADMIN: Can change to any valid status
    - EXPORTER: Can only update their assigned orders
    - CUSTOMER: Cannot update status

    **Process:**
    1. Verify order exists
    2. Check user has permission
    3. Validate state transition (CD-31.3)
    4. Check prerequisites (CD-31.4)
    5. Update order status
    6. Log status change (CD-31.6)
    7. Send notifications (CD-31.7)

    **Returns:**
    - Updated order
    - New status
    - Status history entry
    """

    print("\n" + "=" * 70)
    print("🔄 STATUS UPDATE REQUEST")
    print(f"   User: {current_user.email} ({current_user.role})")
    print(f"   Order: {order_id}")
    print(f"   New Status: {new_status}")
    print("=" * 70 + "\n")

    # ===============================================================
    # STEP 1: VERIFY ORDER EXISTS
    # ===============================================================
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Order {order_id} not found"
        )

    print("✅ STEP 1: Order Found")
    print(f"   Current Status: {order.status.value}")

    # ===============================================================
    # STEP 2: CHECK PERMISSIONS
    # ===============================================================

    # Only admins and exporters can update status
    if current_user.role not in ["ADMIN", "EXPORTER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and exporters can update order status",
        )

    # Exporters can only update their assigned orders
    if current_user.role == "EXPORTER":
        # Check if this exporter is assigned to this order
        from app.modules.shipping.models import ShipmentDetails

        shipment = db.query(ShipmentDetails).filter(ShipmentDetails.order_id == order_id).first()

        if not shipment or shipment.exporter_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update orders assigned to you",
            )

    print("✅ STEP 2: Permissions Verified")

    # ===============================================================
    # STEP 3: VALIDATE NEW STATUS (CD-31.3)
    # ===============================================================

    # Convert string to OrderStatus enum
    try:
        new_status_enum = OrderStatus(new_status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status: {new_status}"
        )

    # Check if already in desired status
    if order.status == new_status_enum:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Order already in {new_status} status"
        )

    print("✅ STEP 3: Status Validated")

    # ===============================================================
    # STEP 4: VALIDATE STATE TRANSITION (CD-31.3, CD-31.4)
    # ===============================================================

    is_valid, error_message = validate_state_transition(
        order=order, new_status=new_status_enum, db=db
    )

    if not is_valid:
        print(f"❌ VALIDATION FAILED: {error_message}")

        # Get allowed next states for helpful error message
        allowed = get_allowed_next_states(order.status)
        allowed_names = [s.value for s in allowed]

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": error_message,
                "current_status": order.status.value,
                "requested_status": new_status,
                "allowed_next_states": allowed_names,
            },
        )

    print("✅ STEP 4: Transition Valid")

    # ===============================================================
    # STEP 5: UPDATE ORDER STATUS
    # ===============================================================

    old_status = order.status
    order.status = new_status_enum

    print("\n✅ STEP 5: Status Updated")
    print(f"   {old_status.value} → {new_status_enum.value}")

    # ===============================================================
    # STEP 6: LOG STATUS CHANGE (CD-31.6)
    # ===============================================================

    status_history_service.create_history_entry(
        db=db,
        order=order,
        from_status=old_status,
        to_status=new_status_enum,
        changed_by=current_user,
        notes=notes or f"Status updated by {current_user.role.lower()}",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    print("\n✅ STEP 6: Status History Created")

    # Commit changes
    db.commit()
    db.refresh(order)

    print("\n" + "=" * 70)
    print("🎉 STATUS UPDATE COMPLETED")
    print(f"   Order: {order.id}")
    print(f"   New Status: {order.status.value}")
    print("=" * 70 + "\n")
    # ===============================================================
    # STEP 7: SEND NOTIFICATIONS (CD-31.7)
    # ===============================================================
    try:
        await send_status_change_notification(
            order=order,
            old_status=old_status,
            new_status=new_status_enum,
        )
    except Exception:
        logger.exception(
            "Status updated for order_id=%s, but notification dispatch failed",
            order.id,
        )

    return {
        "message": "Order status updated successfully",
        "order_id": str(order.id),
        "old_status": old_status.value,
        "new_status": order.status.value,
        "changed_by": current_user.email,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ===================================================================
# ENDPOINT: GET TIMELINE
# ===================================================================


@router.get("/{order_id}/timeline", response_model=OrderTimelineResponse)
async def get_order_timeline(
    order_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get order status timeline.

    **Story**: CD-32.2 - Order timeline endpoint

    **Access**:
    - Customer: Own orders only
    - Staff roles: All orders

    **Returns**:
    - Complete chronological timeline
    - Who changed each status
    - When each change occurred
    - Optional notes for each change

    **Use Case**:
    Customer can track their order journey:
    - Order Created
    - Payment Confirmed
    - Exporter Assigned
    - Shipping Started
    - In Transit
    - Customs Clearance
    - Delivered
    """

    print(f"\n{'=' * 70}")
    print("📋 FETCHING ORDER TIMELINE")
    print(f"   Order: {order_id}")
    print(f"   User: {current_user.email}")
    print(f"{'=' * 70}\n")

    # Get order
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # Customers can only see their own orders. Staff roles can view all orders.
    if _customer_must_own_order(order, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Get timeline
    history_records = status_history_service.get_order_timeline(db, order_id)

    # Build response
    timeline = []

    for record in history_records:
        actor_name = "System"
        actor_email = "system@cleardrive.local"
        if record.user is not None:
            actor_name = record.user.name or record.user.email
            actor_email = record.user.email

        timeline_item = OrderStatusHistoryResponse(
            id=record.id,
            order_id=record.order_id,
            from_status=record.from_status,
            to_status=record.to_status,
            notes=record.notes,
            changed_by_id=record.changed_by,
            changed_by_name=actor_name,
            changed_by_email=actor_email,
            created_at=record.created_at,
        )
        timeline.append(timeline_item)

    print(f"✅ Timeline fetched: {len(timeline)} events")
    print(f"{'=' * 70}\n")

    return OrderTimelineResponse(
        order_id=order.id,
        current_status=order.status.value,
        created_at=order.created_at,
        total_events=len(timeline),
        timeline=timeline,
    )


@router.get("/{order_id}/timeline/stream")
async def stream_order_timeline(
    order_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Stream timeline updates as Server-Sent Events.

    CD-32.5: push timeline refresh signals to the frontend when order status
    history changes.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if _customer_must_own_order(order, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    def snapshot() -> dict[str, str | int]:
        history_count = (
            db.query(func.count(OrderStatusHistory.id))
            .filter(OrderStatusHistory.order_id == order.id)
            .scalar()
            or 0
        )
        latest_history_at = (
            db.query(func.max(OrderStatusHistory.created_at))
            .filter(OrderStatusHistory.order_id == order.id)
            .scalar()
        )
        return {
            "status": order.status.value,
            "history_count": int(history_count),
            "latest_history_at": latest_history_at.isoformat() if latest_history_at else "",
        }

    async def event_stream():
        last_snapshot = snapshot()
        yield f"event: timeline\ndata: {json.dumps(last_snapshot)}\n\n"

        while True:
            if await request.is_disconnected():
                break

            db.expire_all()
            current_snapshot = snapshot()
            if current_snapshot != last_snapshot:
                last_snapshot = current_snapshot
                yield f"event: timeline\ndata: {json.dumps(current_snapshot)}\n\n"

            yield ": keepalive\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ===================================================================
# ENDPOINT: GET ALLOWED NEXT STATES
# ===================================================================


@router.get("/{order_id}/allowed-transitions")
async def get_order_allowed_transitions(
    order_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get list of allowed next states for this order.

    Useful for frontend to show only valid action buttons.

    **Returns:**
    - Current status
    - List of allowed next states
    - Prerequisites for each state
    """

    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Order {order_id} not found"
        )

    # Customers can only inspect their own orders. Staff roles can inspect all.
    if _customer_must_own_order(order, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this order",
        )

    # Get allowed next states
    allowed_states = get_allowed_next_states(order.status)

    # Check prerequisites for each allowed state
    transitions = []
    for next_state in allowed_states:
        is_valid, error_msg = validate_state_transition(order, next_state, db)

        transitions.append(
            {
                "status": next_state.value,
                "can_transition": is_valid,
                "reason": error_msg if not is_valid else None,
            }
        )

    return {
        "order_id": str(order.id),
        "current_status": order.status.value,
        "allowed_transitions": transitions,
    }
