# backend/app/modules/notifications/service.py

"""
Notification service for order status changes.
Author: Tharin
Story: CD-31.7 - Notification triggers on status change
"""

from app.modules.orders.models import Order, OrderStatus

# TODO: Implement email service when ready


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

    # Mapping: status → notification function
    notifications = {
        OrderStatus.PAYMENT_CONFIRMED: notify_payment_confirmed,
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
    print(f"📧 TODO: Send payment confirmation email to {order.user.email}")
    # await send_email(
    #     to=order.user.email,
    #     subject="Payment Confirmed - ClearDrive.lk",
    #     template="payment_confirmed",
    #     data={"order_id": str(order.id), "total": order.total_cost_lkr}
    # )


async def notify_exporter_assigned(order: Order, old_status: OrderStatus):
    """Notify exporter of new assignment."""
    print("📧 TODO: Send assignment email to exporter")
    # Get exporter from shipment details
    # await send_email(...)


async def notify_shipped(order: Order, old_status: OrderStatus):
    """Notify customer that vehicle has shipped."""
    print(f"📧 TODO: Send shipping notification to {order.user.email}")
    # Include tracking info, vessel details, ETA
    # await send_email(...)


async def notify_delivered(order: Order, old_status: OrderStatus):
    """Notify customer of delivery, request feedback."""
    print(f"📧 TODO: Send delivery confirmation + survey to {order.user.email}")
    # await send_email(...)


async def notify_cancelled(order: Order, old_status: OrderStatus):
    """Notify customer of cancellation."""
    print(f"📧 TODO: Send cancellation email to {order.user.email}")
    # Include reason, refund info
    # await send_email(...)
