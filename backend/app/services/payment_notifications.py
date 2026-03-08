"""Payment notification stubs (CD-42.6)."""

from __future__ import annotations

import logging

from app.modules.orders.models import Order
from app.modules.payments.models import Payment

logger = logging.getLogger(__name__)


async def send_payment_confirmation_email(payment: Payment, order: Order) -> None:
    """Stub for success email integration."""
    logger.info(
        "[TODO] send payment confirmation email: order_id=%s payment_id=%s amount=%s %s",
        order.id,
        payment.id,
        payment.amount,
        payment.currency,
    )


async def send_payment_failure_email(payment: Payment, order: Order) -> None:
    """Stub for failure email integration."""
    logger.info(
        "[TODO] send payment failure email: order_id=%s payment_id=%s status=%s",
        order.id,
        payment.id,
        payment.status,
    )
