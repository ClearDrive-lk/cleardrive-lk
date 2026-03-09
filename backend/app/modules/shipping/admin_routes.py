"""Admin shipping endpoints.

Author: Kalidu
Story: CD-70 - Exporter Assignment
"""

from __future__ import annotations

import logging

from app.core.database import get_db
from app.core.permissions import Permission, require_permission
from app.modules.auth.models import Role, User
from app.modules.notifications.service import send_status_change_notification
from app.modules.orders.models import Order, OrderStatus
from app.modules.shipping.models import ShipmentDetails
from app.modules.shipping.schemas import (
    AssignableOrderItem,
    ExporterAssignment,
    ShippingDetailsResponse,
)
from app.services.orders.status_history import status_history_service
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/shipping", tags=["admin-shipping"])


@router.post("/{order_id}/assign", response_model=ShippingDetailsResponse)
async def assign_exporter_to_order(
    order_id: str,
    assignment: ExporterAssignment,
    request: Request,
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

    status_history_service.create_history_entry(
        db=db,
        order=order,
        from_status=old_status,
        to_status=OrderStatus.ASSIGNED_TO_EXPORTER,
        changed_by=current_user,
        notes=f"Assigned to exporter: {exporter.email}",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    db.commit()
    db.refresh(shipment)

    try:
        await send_status_change_notification(
            order=order,
            old_status=old_status,
            new_status=OrderStatus.ASSIGNED_TO_EXPORTER,
        )
    except Exception:
        logger.exception(
            "Exporter assignment completed for order_id=%s, but notification dispatch failed",
            order.id,
        )

    return shipment


@router.get("/assignable-orders", response_model=list[AssignableOrderItem])
async def list_assignable_orders(
    current_user: User = Depends(require_permission(Permission.MANAGE_ORDERS)),
    db: Session = Depends(get_db),
):
    """List paid orders that can be assigned to an exporter."""
    orders = (
        db.query(Order)
        .filter(Order.status == OrderStatus.PAYMENT_CONFIRMED)
        .order_by(Order.created_at.desc())
        .all()
    )

    assignable_orders: list[AssignableOrderItem] = []
    for order in orders:
        if order.shipment_details is not None:
            continue

        vehicle = getattr(order, "vehicle", None)
        user = getattr(order, "user", None)
        vehicle_label = "Vehicle details unavailable"
        if vehicle is not None:
            vehicle_label = f"{vehicle.make} {vehicle.model} {vehicle.year}".strip()

        assignable_orders.append(
            AssignableOrderItem(
                id=order.id,
                customer_name=(getattr(user, "name", None) or "Unknown customer"),
                customer_email=(getattr(user, "email", None) or "Unknown email"),
                vehicle_label=vehicle_label,
                status=order.status.value,
                payment_status=order.payment_status.value,
                total_cost_lkr=(
                    float(order.total_cost_lkr) if order.total_cost_lkr is not None else None
                ),
                created_at=order.created_at,
            )
        )

    return assignable_orders


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
