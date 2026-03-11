"""Payment notification helpers for PayHere webhooks."""

from __future__ import annotations

import logging
from html import escape

from app.modules.orders.models import Order
from app.modules.payments.models import Payment
from app.services.email import send_email
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)


async def send_payment_confirmation_email(payment: Payment, order: Order) -> None:
    """Send payment confirmation email to the customer."""
    user = getattr(order, "user", None)
    recipient = getattr(user, "email", None)
    if not recipient:
        logger.warning(
            "Payment confirmation email skipped: missing customer email for order_id=%s", order.id
        )
        return

    receipt_id = payment.payhere_payment_id or str(payment.id)
    payment_date = payment.completed_at.strftime("%Y-%m-%d %H:%M:%S") if payment.completed_at else "Unknown"

    email_sent_id = await notification_service.send_payment_confirmation(
        email=recipient,
        user_name=getattr(user, "name", "Customer") or "Customer",
        order_id=str(order.id),
        amount=f"{payment.amount} {payment.currency}",
        receipt_id=receipt_id,
        payment_date=payment_date,
        payment_method=payment.payment_method or "Not available"
    )

    if not email_sent_id:
        logger.warning(
            "Payment confirmation email failed: order_id=%s payment_id=%s amount=%s %s",
            order.id,
            payment.id,
            payment.amount,
            payment.currency,
        )

async def send_payment_failure_email(payment: Payment, order: Order) -> None:
    """Send payment failure email to the customer."""
    user = getattr(order, "user", None)
    recipient = getattr(user, "email", None)
    if not recipient:
        logger.warning(
            "Payment failure email skipped: missing customer email for order_id=%s", order.id
        )
        return

    subject = "Payment Failed - ClearDrive.lk"
    html_content = (
        "<h2>Payment Failed</h2>"
        f"<p>We could not confirm payment for order <strong>{escape(str(order.id))}</strong>.</p>"
        f"<p>Status: {escape(payment.status.value)}</p>"
        "<p>Please try again or contact your bank if the issue continues.</p>"
    )
    text_content = (
        "Payment Failed\n\n"
        f"Order: {order.id}\n"
        f"Status: {payment.status.value}\n\n"
        "Please try again or contact your bank if the issue continues."
    )

    sent = await send_email(recipient, subject, html_content, text_content)
    if not sent:
        logger.warning(
            "Payment failure email failed: order_id=%s payment_id=%s status=%s",
            order.id,
            payment.id,
            payment.status,
        )
