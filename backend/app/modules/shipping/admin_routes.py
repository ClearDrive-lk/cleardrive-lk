"""Admin shipping endpoints.

Author: Kalidu
Story: CD-70 - Exporter Assignment
"""

import logging
from datetime import datetime
from uuid import UUID

from app.core.database import get_db
from app.core.permissions import Permission, require_permission
from app.modules.auth.models import Role, User
from app.modules.notifications.service import send_status_change_notification
from app.modules.orders.models import Order, OrderStatus
from app.modules.shipping.models import DocumentType, ShipmentDetails, ShipmentStatus
from app.modules.shipping.schemas import (
    AssignableOrderItem,
    ExporterAssignment,
    ShippingDetailsResponse,
)
from app.modules.vehicles.models import Vehicle
from app.services.notification_service import notification_service
from app.services.orders.status_history import status_history_service
from fastapi import APIRouter, Depends, HTTPException, Request, status
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

    items: list[AssignableOrderItem] = []
    for order in orders:
        user = db.query(User).filter(User.id == order.user_id).first()
        vehicle = db.query(Vehicle).filter(Vehicle.id == order.vehicle_id).first()

        if user is None or vehicle is None:
            logger.warning(
                "Skipping assignable order with missing relations order_id=%s user_id=%s vehicle_id=%s",
                order.id,
                order.user_id,
                order.vehicle_id,
            )
            continue

        items.append(
            AssignableOrderItem(
                id=order.id,
                user_id=order.user_id,
                vehicle_id=order.vehicle_id,
                customer_name=user.name or user.email,
                customer_email=user.email,
                vehicle_label=f"{vehicle.make} {vehicle.model} ({vehicle.year})",
                status=order.status.value,
                payment_status=order.payment_status.value,
                total_cost_lkr=(
                    float(order.total_cost_lkr) if order.total_cost_lkr is not None else None
                ),
                created_at=order.created_at,
            )
        )

    return items


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


@router.get("/pending", response_model=list[ShippingDetailsResponse])
async def get_pending_shipments(
    current_user: User = Depends(require_permission(Permission.MANAGE_ORDERS)),
    db: Session = Depends(get_db),
):
    """Get shipments that are ready for admin approval (CD-73.1)."""
    _ = current_user
    shipments = (
        db.query(ShipmentDetails)
        .filter(ShipmentDetails.submitted_at.isnot(None))
        .filter(ShipmentDetails.documents_uploaded.is_(True))
        .filter(ShipmentDetails.approved.is_(False))
        .filter(ShipmentDetails.status == ShipmentStatus.AWAITING_ADMIN_APPROVAL)
        .order_by(ShipmentDetails.submitted_at.asc())
        .all()
    )
    return shipments


@router.post("/{shipment_id}/approve", response_model=ShippingDetailsResponse)
async def approve_shipment(
    shipment_id: UUID,
    request: Request,
    current_user: User = Depends(require_permission(Permission.MANAGE_ORDERS)),
    db: Session = Depends(get_db),
):
    """Approve shipment and update order status (CD-73.2 - CD-73.4)."""
    shipment = db.query(ShipmentDetails).filter(ShipmentDetails.id == shipment_id).first()
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment {shipment_id} not found",
        )

    if shipment.approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shipment already approved",
        )

    if shipment.submitted_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shipping details have not been submitted",
        )

    if not shipment.documents_uploaded:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shipping documents have not been uploaded",
        )

    missing_docs = _get_missing_required_documents(shipment)
    if missing_docs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required documents: {', '.join(missing_docs)}",
        )

    order = shipment.order
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order for shipment {shipment_id} not found",
        )

    shipment.approved = True
    shipment.admin_approved_at = datetime.utcnow()
    shipment.admin_approved_by = current_user.id
    shipment.status = ShipmentStatus.CONFIRMED_SHIPPED
    shipment.updated_at = datetime.utcnow()

    old_status = order.status
    order.status = OrderStatus.SHIPPED

    status_history_service.create_history_entry(
        db=db,
        order=order,
        from_status=old_status,
        to_status=OrderStatus.SHIPPED,
        changed_by=current_user,
        notes="Shipment approved by admin",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    db.commit()
    db.refresh(shipment)

    try:
        await send_status_change_notification(order, old_status, OrderStatus.SHIPPED)
    except Exception:
        logger.exception(
            "Failed to send customer shipment notification for order_id=%s",
            order.id,
        )

    exporter = getattr(shipment, "exporter", None)
    exporter_email = getattr(exporter, "email", None)
    if exporter_email:
        eta_label = (
            shipment.estimated_arrival_date.strftime("%Y-%m-%d")
            if shipment.estimated_arrival_date
            else "TBD"
        )
        try:
            await notification_service._enqueue_template(
                to_email=exporter_email,
                subject=f"Shipment Approved for Order #{order.id}",
                template_name="status_change.html",
                context={
                    "user_name": exporter.name or "Exporter",
                    "order_id": str(order.id),
                    "new_status": "Shipment Approved",
                    "status_message": (
                        "Shipment approved by admin. "
                        f"Vessel: {shipment.vessel_name or 'TBD'}, ETA: {eta_label}."
                    ),
                },
                priority=4,
            )
        except Exception:
            logger.exception(
                "Failed to send exporter shipment approval for order_id=%s",
                order.id,
            )
    return shipment


def _get_missing_required_documents(shipment: ShipmentDetails) -> list[str]:
    required_types = {
        DocumentType.BILL_OF_LADING,
        DocumentType.COMMERCIAL_INVOICE,
        DocumentType.PACKING_LIST,
        DocumentType.EXPORT_CERTIFICATE,
    }
    uploaded_types = {doc.document_type for doc in shipment.documents}
    missing = required_types - uploaded_types
    return [doc_type.value for doc_type in sorted(missing, key=lambda item: item.value)]


@router.get("/{shipment_id}", response_model=ShippingDetailsResponse)
async def get_shipment_details(
    shipment_id: UUID,
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
