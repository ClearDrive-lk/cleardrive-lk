"""Payment notification helpers for PayHere webhooks."""

from __future__ import annotations

import logging
from html import escape

from app.modules.orders.models import Order
from app.modules.payments.models import Payment
from app.services.email import send_email

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

    masked_card = f"**** {payment.card_no}" if payment.card_no else "Not available"
    subject = "Payment Confirmed - ClearDrive.lk"
    html_content = (
        "<h2>Payment Confirmed</h2>"
        f"<p>Your payment for order <strong>{escape(str(order.id))}</strong> has been confirmed.</p>"
        "<p>Payment details:</p>"
        "<ul>"
        f"<li>Amount: {escape(str(payment.amount))} {escape(payment.currency)}</li>"
        f"<li>Method: {escape(payment.payment_method or 'Not available')}</li>"
        f"<li>Card: {escape(masked_card)}</li>"
        "</ul>"
        "<p>Next step: our team will review your order and assign an exporter.</p>"
    )
    text_content = (
        "Payment Confirmed\n\n"
        f"Order: {order.id}\n"
        f"Amount: {payment.amount} {payment.currency}\n"
        f"Method: {payment.payment_method or 'Not available'}\n"
        f"Card: {masked_card}\n\n"
        "Next step: our team will review your order and assign an exporter."
    )

    sent = await send_email(recipient, subject, html_content, text_content)
    if not sent:
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
