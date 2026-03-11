"""
Notification service for order status changes.
Author: Tharin
Story: CD-31.7 - Notification triggers on status change
"""

import logging

from app.modules.orders.models import Order, OrderStatus
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)


async def send_status_change_notification(
    order: Order, old_status: OrderStatus, new_status: OrderStatus
):
    """
    Send notification based on status change.

    Different statuses trigger different notifications:
    - PAYMENT_CONFIRMED: Thank customer, explain next steps
    - ASSIGNED_TO_EXPORTER: Notify exporter of assignment
    - SHIPPED: Notify customer with tracking info
    - DELIVERED: Request customer feedback/review
    """

    # We use notification_service.send_status_change to send the general status updates

    status_messages = {
        OrderStatus.PAYMENT_CONFIRMED: "Your payment is confirmed. We will assign an exporter and keep you updated.",
        OrderStatus.LC_REQUESTED: "Your order is now under LC review.",
        OrderStatus.LC_APPROVED: "Your LC has been approved.",
        OrderStatus.LC_REJECTED: "Your LC was rejected.",
        OrderStatus.ASSIGNED_TO_EXPORTER: "An exporter was assigned to your order.",
        OrderStatus.SHIPPED: "Your order has been marked as shipped.",
        OrderStatus.DELIVERED: "Your order has been delivered. Thank you for choosing ClearDrive.lk.",
        OrderStatus.CANCELLED: "Your order was cancelled.",
    }

    # Exporter-specific assignment notification is handled via a generic email send from NotificationService
    # or just through the generic status_change template.
    if new_status == OrderStatus.ASSIGNED_TO_EXPORTER:
        exporter_email = None
        if order.shipment_details:
            exporter = getattr(order.shipment_details, "exporter", None)
            exporter_email = getattr(exporter, "email", None)

        if exporter_email:
            try:
                # We can enqueue a simple status change for the exporter as well
                await notification_service._enqueue_template(
                    to_email=exporter_email,
                    subject="New Export Assignment - ClearDrive.lk",
                    template_name="status_change.html",
                    context={
                        "user_name": "Exporter",
                        "order_id": str(order.id),
                        "new_status": "Assigned",
                        "status_message": f"You have been assigned to export Order #{order.id}.",
                    },
                    priority=4,
                )
            except Exception as e:
                logger.warning(f"Failed to send assignment to exporter: {str(e)}")

    msg = status_messages.get(new_status)
    if msg and order.user and getattr(order.user, "email", None):
        try:
            await notification_service.send_status_change(
                email=order.user.email,
                user_name=order.user.name or "Customer",
                order_id=str(order.id),
                new_status=new_status.value.replace("_", " ").title(),
                status_message=msg,
            )
        except Exception as e:
            logger.warning(
                "Failed to send status change notification for order_id=%s: %s", order.id, str(e)
            )
