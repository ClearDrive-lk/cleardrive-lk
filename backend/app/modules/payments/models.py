# backend/app/modules/payments/models.py

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID as PyUUID

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum
from app.core.database import Base
from app.core.models import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.modules.orders.models import Order


class PaymentStatus(str, enum.Enum):
    """Payment status enum."""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class Payment(Base, UUIDMixin, TimestampMixin):
    """Payment model - PayHere payments."""

    __tablename__ = "payments"

    # References
    order_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # PayHere details
    payhere_payment_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    # Payment info
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="LKR", nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(SQLEnum(PaymentStatus), nullable=False, index=True)

    # Timestamps
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    order: Mapped[Order] = relationship("Order", back_populates="payment")

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
    """Payment idempotency tracking."""

    __tablename__ = "payment_idempotency"

    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response_data: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self):
        return f"<PaymentIdempotency {self.idempotency_key}>"
