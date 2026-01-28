# backend/app/modules/payments/models.py

from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Enum as SQLEnum, Index, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum
from app.core.database import Base
from app.core.models import TimestampMixin, UUIDMixin


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
    order_id = Column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # PayHere details
    payhere_payment_id = Column(String(255), unique=True, index=True)
    idempotency_key = Column(String(255), unique=True, nullable=False, index=True)

    # Payment info
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="LKR", nullable=False)
    status = Column(SQLEnum(PaymentStatus), nullable=False, index=True)

    # Timestamps
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    order = relationship("Order", back_populates="payment")

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

    idempotency_key = Column(String(255), unique=True, nullable=False, index=True)
    request_hash = Column(String(64), nullable=False)
    response_data = Column(JSONB)
    status = Column(String(50), nullable=False)
    completed_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<PaymentIdempotency {self.idempotency_key}>"
