"""Admin shipping endpoints.

Author: Kalidu
Story: CD-70 - Exporter Assignment
"""

import logging

from app.core.database import get_db
from app.core.permissions import Permission, require_permission
from app.modules.auth.models import Role, User
from app.modules.notifications.service import send_status_change_notification
from app.modules.orders.models import Order, OrderStatus, OrderStatusHistory
from app.modules.shipping.models import ShipmentDetails
from app.modules.shipping.schemas import (
    AssignableOrderItem,
    ExporterAssignment,
    ShippingDetailsResponse,
)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/admin/shipping", tags=["admin-shipping"])
logger = logging.getLogger(__name__)


@router.get("/assignable-orders", response_model=list[AssignableOrderItem])
async def get_assignable_orders(
    current_user: User = Depends(require_permission(Permission.MANAGE_ORDERS)),
    db: Session = Depends(get_db),
):
    """List orders eligible for exporter assignment."""
    _ = current_user
    orders = (
        db.query(Order)
        .outerjoin(ShipmentDetails, ShipmentDetails.order_id == Order.id)
        .filter(Order.status == OrderStatus.PAYMENT_CONFIRMED)
        .filter(ShipmentDetails.id.is_(None))
        .order_by(Order.created_at.desc())
        .all()
    )
    return orders


@router.post("/{order_id}/assign", response_model=ShippingDetailsResponse)
async def assign_exporter_to_order(
    order_id: str,
    assignment: ExporterAssignment,
    current_user: User = Depends(require_permission(Permission.MANAGE_ORDERS)),
    db: Session = Depends(get_db),
):
    """Assign exporter to a paid order."""

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
    if order.status != OrderStatus.PAYMENT_CONFIRMED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order must be in PAYMENT_CONFIRMED status. Current: {order.status}",
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
    db.refresh(order)
    db.refresh(shipment)

    try:
        await send_status_change_notification(
            order=order,
            old_status=old_status,
            new_status=OrderStatus.ASSIGNED_TO_EXPORTER,
        )
    except Exception:
        logger.exception(
            "Exporter assignment notification dispatch failed for order_id=%s",
            order.id,
        )
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
