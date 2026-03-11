"""Exporter shipping endpoints."""

from __future__ import annotations

import datetime as dt
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_exporter
from app.modules.auth.models import Role, User
from app.modules.orders.models import Order, OrderStatus, OrderStatusHistory
from app.modules.shipping.models import ShipmentDetails, ShipmentStatus
from app.modules.shipping.schemas import ShippingDetailsResponse, ShippingDetailsSubmit
from app.services.notification_service import notification_service
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/shipping", tags=["shipping"])


@router.post("/{order_id}/details", response_model=ShippingDetailsResponse)
async def submit_shipping_details(
    order_id: str,
    details: ShippingDetailsSubmit,
    current_user: User = Depends(get_current_exporter),
    db: Session = Depends(get_db),
):
    """Submit shipping details for an exporter-assigned order (CD-71)."""
    try:
        order_uuid = UUID(order_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid order id: {order_id}",
        )

    shipment = db.query(ShipmentDetails).filter(ShipmentDetails.order_id == order_uuid).first()
    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment details not found for order {order_id}",
        )

    if current_user.role != Role.ADMIN and shipment.exporter_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can submit details only for your assigned orders",
        )

    order = db.query(Order).filter(Order.id == order_uuid).first()
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )

    if order.status not in (
        OrderStatus.ASSIGNED_TO_EXPORTER,
        OrderStatus.AWAITING_SHIPMENT_CONFIRMATION,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Shipping details can be submitted only when order status is "
                "ASSIGNED_TO_EXPORTER or AWAITING_SHIPMENT_CONFIRMATION"
            ),
        )

    shipment.vessel_name = details.vessel_name
    shipment.vessel_registration = details.vessel_registration
    shipment.voyage_number = details.voyage_number
    shipment.departure_port = details.departure_port
    shipment.arrival_port = details.arrival_port
    shipment.departure_date = details.departure_date
    shipment.estimated_arrival_date = details.estimated_arrival_date
    shipment.container_number = details.container_number
    shipment.bill_of_landing_number = details.bill_of_landing_number
    shipment.seal_number = details.seal_number
    shipment.tracking_number = details.tracking_number
    shipment.submitted_at = dt.datetime.now(dt.UTC)
    shipment.status = ShipmentStatus.AWAITING_ADMIN_APPROVAL

    old_status = order.status
    order.status = OrderStatus.AWAITING_SHIPMENT_CONFIRMATION

    if old_status != order.status:
        db.add(
            OrderStatusHistory(
                order_id=order.id,
                from_status=old_status,
                to_status=order.status,
                changed_by=current_user.id,
                notes="Shipping details submitted by exporter",
            )
        )

    db.commit()
    db.refresh(shipment)
    db.refresh(order)
    
    # Notify customer about shipment details
    if order.user:
        try:
            await notification_service.send_shipment_notification(
                email=order.user.email,
                user_name=order.user.name or "Customer",
                order_id=str(order.id),
                vessel_name=shipment.vessel_name,
                tracking_number=shipment.tracking_number or "Pending",
                estimated_arrival=shipment.estimated_arrival_date.strftime("%Y-%m-%d") if shipment.estimated_arrival_date else "TBD"
            )
        except Exception:
            pass

    return shipment
