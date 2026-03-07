"""Admin shipping endpoints.

Author: Kalidu
Story: CD-70 - Exporter Assignment
"""

from app.core.database import get_db
from app.core.permissions import Permission, require_permission
from app.modules.auth.models import Role, User
from app.modules.orders.models import Order, OrderStatus, OrderStatusHistory
from app.modules.shipping.models import ShipmentDetails
from app.modules.shipping.schemas import ExporterAssignment, ShippingDetailsResponse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/admin/shipping", tags=["admin-shipping"])


@router.post("/{order_id}/assign", response_model=ShippingDetailsResponse)
async def assign_exporter_to_order(
    order_id: str,
    assignment: ExporterAssignment,
    current_user: User = Depends(require_permission(Permission.MANAGE_ORDERS)),
    db: Session = Depends(get_db),
):
    """Assign exporter to a paid order."""
    """
    Assign exporter to a paid order.

    **Story**: CD-70 - Exporter Assignment

    **Permissions**: MANAGE_ORDERS (Admin only)

    **Prerequisites:**
    - Order must exist
    - Order status must be LC_APPROVED
    - Exporter user must have EXPORTER role
    - Order must not already have exporter assigned

    **Process:**
    1. Verify order exists and status is LC_APPROVED
    2. Verify exporter exists and has EXPORTER role
    3. Create shipment_details record (CD-70.3)
    4. Update order status to ASSIGNED_TO_EXPORTER (CD-70.2)
    5. Create order status history entry
    6. Send email to exporter (CD-70.4) - TODO

    **Returns:**
    - Created shipment details
    - Order status updated
    - Exporter assigned
    """

    print(f"\n{'=' * 70}")
    print("📦 EXPORTER ASSIGNMENT STARTED")
    print(f"   Admin: {current_user.email}")
    print(f"   Order ID: {order_id}")
    print(f"{'=' * 70}\n")

    # ===============================================================
    # STEP 1: VERIFY ORDER EXISTS AND STATUS
    # ===============================================================
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )

    # Check order status
    if order.status != OrderStatus.LC_APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order must be in LC_APPROVED status. Current: {order.status}",
        )

    existing_shipment = (
        db.query(ShipmentDetails).filter(ShipmentDetails.order_id == order_id).first()
    )
    if existing_shipment:
        exporter_label = (
            existing_shipment.exporter.email
            if getattr(existing_shipment, "exporter", None) is not None
            else str(existing_shipment.assigned_exporter_id)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order already has an exporter assigned: {exporter_label}",
        )

    exporter = db.query(User).filter(User.id == assignment.exporter_id).first()
    if not exporter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exporter {assignment.exporter_id} not found",
        )

    if exporter.role != Role.EXPORTER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User {exporter.email} is not an exporter. Role: {exporter.role}",
        )

    shipment = ShipmentDetails(order_id=order.id, assigned_exporter_id=exporter.id)
    db.add(shipment)
    db.flush()

    old_status = order.status
    order.status = OrderStatus.ASSIGNED_TO_EXPORTER

    history = OrderStatusHistory(
        order_id=order.id,
        from_status=old_status,
        to_status=OrderStatus.ASSIGNED_TO_EXPORTER,
        changed_by=current_user.id,
        notes=f"Assigned to exporter: {exporter.email}",
    )
    db.add(history)

    db.commit()
    db.refresh(shipment)
    return shipment


@router.get("/all")
async def get_all_shipments(
    current_user: User = Depends(require_permission(Permission.MANAGE_ORDERS)),
    db: Session = Depends(get_db),
):
    """Get all shipments (admin view)."""
    all_shipments = db.query(ShipmentDetails).all()

    awaiting_details = []
    awaiting_approval = []
    approved = []

    for shipment in all_shipments:
        if not shipment.vessel_name:
            awaiting_details.append(shipment)
        elif not shipment.documents_uploaded:
            awaiting_details.append(shipment)
        elif not shipment.approved:
            awaiting_approval.append(shipment)
        else:
            approved.append(shipment)

    return {
        "total": len(all_shipments),
        "awaiting_details": len(awaiting_details),
        "awaiting_approval": len(awaiting_approval),
        "approved": len(approved),
        "shipments": all_shipments,
    }


@router.get("/{shipment_id}", response_model=ShippingDetailsResponse)
async def get_shipment_details(
    shipment_id: str,
    current_user: User = Depends(require_permission(Permission.MANAGE_ORDERS)),
    db: Session = Depends(get_db),
):
    """Get detailed shipment information."""
    shipment = db.query(ShipmentDetails).filter(ShipmentDetails.id == shipment_id).first()
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment {shipment_id} not found",
        )
    return shipment
