# backend/app/modules/notifications/service.py

"""
Notification service for order status changes.
Author: Tharin
Story: CD-31.7 - Notification triggers on status change
"""

import logging

from app.modules.orders.models import Order, OrderStatus
from app.services.email import send_email

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

    notifications = {
        OrderStatus.PAYMENT_CONFIRMED: notify_payment_confirmed,
        OrderStatus.LC_REQUESTED: notify_lc_requested,
        OrderStatus.LC_APPROVED: notify_lc_approved,
        OrderStatus.LC_REJECTED: notify_lc_rejected,
        OrderStatus.ASSIGNED_TO_EXPORTER: notify_exporter_assigned,
        OrderStatus.SHIPPED: notify_shipped,
        OrderStatus.DELIVERED: notify_delivered,
        OrderStatus.CANCELLED: notify_cancelled,
    }

    notification_fn = notifications.get(new_status)
    if notification_fn:
        await notification_fn(order, old_status)


async def notify_payment_confirmed(order: Order, old_status: OrderStatus):
    """Notify customer that payment was confirmed."""
    subject = "Payment Confirmed - ClearDrive.lk"
    html_content = (
        "<h2>Payment Confirmed</h2>"
        f"<p>Your payment for order <strong>{order.id}</strong> is confirmed.</p>"
        "<p>We will assign an exporter and keep you updated.</p>"
    )
    text_content = (
        "Payment Confirmed\n\n"
        f"Your payment for order {order.id} is confirmed.\n"
        "We will assign an exporter and keep you updated."
    )
    sent = await send_email(order.user.email, subject, html_content, text_content)
    if not sent:
        logger.warning("Failed to send PAYMENT_CONFIRMED notification for order_id=%s", order.id)


async def notify_exporter_assigned(order: Order, old_status: OrderStatus):
    """Notify exporter of new assignment."""
    exporter_email = None
    if order.shipment_details:
        exporter = getattr(order.shipment_details, "exporter", None)
        exporter_email = getattr(exporter, "email", None)

    if not exporter_email:
        logger.warning(
            "Exporter email missing for order_id=%s, sending customer update instead",
            order.id,
        )
        subject = "Exporter Assigned - ClearDrive.lk"
        html_content = (
            "<h2>Exporter Assigned</h2>"
            f"<p>An exporter was assigned to your order <strong>{order.id}</strong>.</p>"
        )
        text_content = "Exporter Assigned\n\n" f"An exporter was assigned to your order {order.id}."
        sent = await send_email(order.user.email, subject, html_content, text_content)
        if not sent:
            logger.warning(
                "Failed to send ASSIGNED_TO_EXPORTER customer fallback for order_id=%s",
                order.id,
            )
        return

    subject = "New Export Assignment - ClearDrive.lk"
    html_content = (
        "<h2>New Export Assignment</h2>"
        f"<p>You have been assigned to order <strong>{order.id}</strong>.</p>"
    )
    text_content = "New Export Assignment\n\n" f"You have been assigned to order {order.id}."
    sent = await send_email(exporter_email, subject, html_content, text_content)
    if not sent:
        logger.warning(
            "Failed to send ASSIGNED_TO_EXPORTER notification for order_id=%s",
            order.id,
        )


async def notify_lc_requested(order: Order, old_status: OrderStatus):
    """Notify customer that LC process has started."""
    subject = "LC Review Started - ClearDrive.lk"
    html_content = (
        "<h2>LC Review Started</h2>"
        f"<p>Your order <strong>{order.id}</strong> is now under LC review.</p>"
    )
    text_content = "LC Review Started\n\n" f"Your order {order.id} is now under LC review."
    sent = await send_email(order.user.email, subject, html_content, text_content)
    if not sent:
        logger.warning("Failed to send LC_REQUESTED notification for order_id=%s", order.id)


async def notify_lc_approved(order: Order, old_status: OrderStatus):
    """Notify customer that LC was approved."""
    subject = "LC Approved - ClearDrive.lk"
    html_content = (
        "<h2>LC Approved</h2>"
        f"<p>Your LC for order <strong>{order.id}</strong> has been approved.</p>"
    )
    text_content = "LC Approved\n\n" f"Your LC for order {order.id} has been approved."
    sent = await send_email(order.user.email, subject, html_content, text_content)
    if not sent:
        logger.warning("Failed to send LC_APPROVED notification for order_id=%s", order.id)


async def notify_lc_rejected(order: Order, old_status: OrderStatus):
    """Notify customer that LC was rejected."""
    subject = "LC Rejected - ClearDrive.lk"
    html_content = (
        "<h2>LC Rejected</h2>" f"<p>Your LC for order <strong>{order.id}</strong> was rejected.</p>"
    )
    text_content = "LC Rejected\n\n" f"Your LC for order {order.id} was rejected."
    sent = await send_email(order.user.email, subject, html_content, text_content)
    if not sent:
        logger.warning("Failed to send LC_REJECTED notification for order_id=%s", order.id)


async def notify_shipped(order: Order, old_status: OrderStatus):
    """Notify customer that vehicle has shipped."""
    subject = "Your Vehicle Has Shipped - ClearDrive.lk"
    html_content = (
        "<h2>Vehicle Shipped</h2>"
        f"<p>Your order <strong>{order.id}</strong> has been marked as shipped.</p>"
    )
    text_content = "Vehicle Shipped\n\n" f"Your order {order.id} has been marked as shipped."
    sent = await send_email(order.user.email, subject, html_content, text_content)
    if not sent:
        logger.warning("Failed to send SHIPPED notification for order_id=%s", order.id)


async def notify_delivered(order: Order, old_status: OrderStatus):
    """Notify customer of delivery, request feedback."""
    subject = "Order Delivered - ClearDrive.lk"
    html_content = (
        "<h2>Order Delivered</h2>"
        f"<p>Your order <strong>{order.id}</strong> has been delivered.</p>"
        "<p>Thank you for choosing ClearDrive.lk.</p>"
    )
    text_content = (
        "Order Delivered\n\n"
        f"Your order {order.id} has been delivered.\n"
        "Thank you for choosing ClearDrive.lk."
    )
    sent = await send_email(order.user.email, subject, html_content, text_content)
    if not sent:
        logger.warning("Failed to send DELIVERED notification for order_id=%s", order.id)


async def notify_cancelled(order: Order, old_status: OrderStatus):
    """Notify customer of cancellation."""
    subject = "Order Cancelled - ClearDrive.lk"
    html_content = (
        "<h2>Order Cancelled</h2>" f"<p>Your order <strong>{order.id}</strong> was cancelled.</p>"
    )
    text_content = "Order Cancelled\n\n" f"Your order {order.id} was cancelled."
    sent = await send_email(order.user.email, subject, html_content, text_content)
    if not sent:
        logger.warning("Failed to send CANCELLED notification for order_id=%s", order.id)
