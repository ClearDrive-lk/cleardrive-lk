# backend/app/modules/payments/models.py
"""
Payment models with idempotency.
Author: Tharin
Epic: CD-E5
Story: CD-40, CD-41
"""

from __future__ import annotations

import datetime as dt
import enum
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID as PyUUID

from app.core.database import Base
from app.core.models import GUID, TimestampMixin, UUIDMixin
from sqlalchemy import JSON, DateTime, Index, Numeric, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.modules.orders.models import Order
    from app.modules.users.models import User


class PaymentStatus(str, enum.Enum):
    """Payment status enum."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class Payment(Base, UUIDMixin, TimestampMixin):
    """
    Payment record with idempotency.
    
    Idempotency layers:
    1. Unique idempotency_key (client-generated)
    2. Unique payhere_payment_id
    3. One COMPLETED payment per order (partial index)
    """

    __tablename__ = "payments"

    # Foreign Keys
    order_id: Mapped[PyUUID] = mapped_column(
        GUID(), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[PyUUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # PayHere Integration
    payhere_payment_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, index=True
    )
    payhere_order_id: Mapped[str | None] = mapped_column(String(255))

    # Idempotency
    idempotency_key: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )

    # Payment Details
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="LKR", nullable=False)

    # Status
    status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING, index=True
    )

    # PayHere Response Data
    payment_method: Mapped[str | None] = mapped_column(String(50))  # VISA, MASTERCARD, etc.
    card_holder_name: Mapped[str | None] = mapped_column(String(255))
    card_no: Mapped[str | None] = mapped_column(String(20))  # Last 4 digits only

    # Timestamps
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    order: Mapped[Order] = relationship("Order", back_populates="payment")
    user: Mapped[User] = relationship("User")

    def __repr__(self):
        return f"<Payment {self.id} - {self.status}>"


# Partial unique index: only one COMPLETED payment per order
Index(
    "idx_one_completed_payment_per_order",
    Payment.order_id,
    unique=True,
    postgresql_where=(Payment.status == PaymentStatus.COMPLETED),
)


class PaymentIdempotency(Base, UUIDMixin, TimestampMixin):
    """
    Track idempotency for payment requests.
    
    Purpose: Prevent duplicate payment processing even if
    user clicks "Pay" button multiple times.
    """

    __tablename__ = "payment_idempotency"

    idempotency_key: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256 of request body
    
    # Response Storage
    response_data: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Timestamps
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self):
        return f"<PaymentIdempotency {self.idempotency_key}>"