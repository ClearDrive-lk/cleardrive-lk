from __future__ import annotations

import enum
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID as PyUUID

from app.core.database import Base
from app.core.models import GUID, TimestampMixin, UUIDMixin
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.modules.auth.models import User
    from app.modules.finance.models import (
        LetterOfCredit,
        VehicleFinance,
        VehicleInsurance,
    )
    from app.modules.payments.models import Payment
    from app.modules.shipping.models import ShipmentDetails
    from app.modules.vehicles.models import Vehicle


class OrderStatus(str, enum.Enum):
    """Order status enum including LC review states."""

    CREATED = "CREATED"
    PAYMENT_CONFIRMED = "PAYMENT_CONFIRMED"
    LC_REQUESTED = "LC_REQUESTED"
    LC_APPROVED = "LC_APPROVED"
    LC_REJECTED = "LC_REJECTED"
    ASSIGNED_TO_EXPORTER = "ASSIGNED_TO_EXPORTER"
    SHIPMENT_DOCS_UPLOADED = "SHIPMENT_DOCS_UPLOADED"
    AWAITING_SHIPMENT_CONFIRMATION = "AWAITING_SHIPMENT_CONFIRMATION"
    SHIPPED = "SHIPPED"
    IN_TRANSIT = "IN_TRANSIT"
    ARRIVED_AT_PORT = "ARRIVED_AT_PORT"
    CUSTOMS_CLEARANCE = "CUSTOMS_CLEARANCE"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, enum.Enum):
    """Payment status enum."""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class Order(Base, UUIDMixin, TimestampMixin):
    """Order model - vehicle import orders."""

    __tablename__ = "orders"
    __table_args__ = (
        Index("idx_orders_created_at", "created_at"),
        Index("idx_orders_status", "status"),
        Index("idx_orders_user_id", "user_id"),
    )

    # References
    user_id: Mapped[PyUUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    vehicle_id: Mapped[PyUUID] = mapped_column(
        GUID(), ForeignKey("vehicles.id"), nullable=False, index=True
    )

    # Status
    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus), default=OrderStatus.CREATED, nullable=False
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False
    )

    # Customer details (encrypted)
    shipping_address: Mapped[str] = mapped_column(Text, nullable=False)  # Encrypted with AES-256
    phone: Mapped[str] = mapped_column(String(20), nullable=False)

    # Pricing
    total_cost_lkr: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))

    # Relationships
    user: Mapped[User] = relationship("User", foreign_keys=[user_id], back_populates="orders")

    vehicle: Mapped[Vehicle] = relationship("Vehicle", back_populates="orders")
    status_history: Mapped[list[OrderStatusHistory]] = relationship(
        "OrderStatusHistory",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderStatusHistory.created_at",
    )
    # Tharin - 09/02/2026
    payments: Mapped[list[Payment]] = relationship(
        "Payment", back_populates="order", cascade="all, delete-orphan"
    )

    shipment_details: Mapped[ShipmentDetails | None] = relationship(
        "ShipmentDetails",
        back_populates="order",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Order {self.id} - {self.status}>"

    # Relationships with financial services
    letter_of_credit: Mapped[LetterOfCredit | None] = relationship(
        "LetterOfCredit", back_populates="order", uselist=False
    )
    vehicle_finance: Mapped[VehicleFinance | None] = relationship(
        "VehicleFinance", back_populates="order", uselist=False
    )
    vehicle_insurance: Mapped[VehicleInsurance | None] = relationship(
        "VehicleInsurance", back_populates="order", uselist=False
    )

    # Inspection fields (Tharin - 10/02/2026)
    # inspection_status: Mapped[str | None] = mapped_column(String(50))
    # inspector_notes: Mapped[str | None] = mapped_column(Text)
    # inspection_images: Mapped[str | None] = mapped_column(Text)  # Store as JSON string
    # inspection_date: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    # inspector_id: Mapped[PyUUID | None] = mapped_column(GUID(), ForeignKey("users.id"))


class OrderStatusHistory(Base, UUIDMixin, TimestampMixin):
    """Order status change history."""

    __tablename__ = "order_status_history"
    __table_args__ = (
        Index("idx_order_status_history_created_at", "created_at"),
        Index("idx_order_status_history_to_status", "to_status"),
    )

    order_id: Mapped[PyUUID] = mapped_column(
        GUID(), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Status change
    from_status: Mapped[OrderStatus | None] = mapped_column(SQLEnum(OrderStatus))
    to_status: Mapped[OrderStatus] = mapped_column(SQLEnum(OrderStatus), nullable=False)

    # Who changed it
    changed_by: Mapped[PyUUID | None] = mapped_column(GUID(), ForeignKey("users.id"))
    notes: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(255))

    # Relationships
    order: Mapped[Order] = relationship("Order", back_populates="status_history")
    user: Mapped["User"] = relationship("User", foreign_keys=[changed_by])

    def __repr__(self):
        return f"<OrderStatusHistory {self.from_status} -> {self.to_status}>"


# Import at the bottom to register models in SQLAlchemy without circular dependencies
import app.modules.finance.models  # noqa: E402, F401
