# backend/app/modules/orders/models.py

from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Text, Enum as SQLEnum, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.core.database import Base
from app.core.models import TimestampMixin, UUIDMixin


class OrderStatus(str, enum.Enum):
    """Order status enum - 11 states."""

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

    # References
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False, index=True)

    # Status
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.CREATED, nullable=False, index=True)
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)

    # Customer details (encrypted)
    shipping_address = Column(Text, nullable=False)  # Encrypted with AES-256
    phone = Column(String(20), nullable=False)

    # Pricing
    total_cost_lkr = Column(Numeric(12, 2))

    # Relationships
    user = relationship("User", back_populates="orders")
    vehicle = relationship("Vehicle", back_populates="orders")
    status_history = relationship(
        "OrderStatusHistory", back_populates="order", cascade="all, delete-orphan"
    )
    payment = relationship(
        "Payment", back_populates="order", uselist=False, cascade="all, delete-orphan"
    )
    shipment_details = relationship(
        "ShipmentDetails", back_populates="order", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Order {self.id} - {self.status}>"


class OrderStatusHistory(Base, UUIDMixin, TimestampMixin):
    """Order status change history."""

    __tablename__ = "order_status_history"

    order_id = Column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Status change
    from_status = Column(SQLEnum(OrderStatus))
    to_status = Column(SQLEnum(OrderStatus), nullable=False)

    # Who changed it
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    notes = Column(Text)

    # Relationships
    order = relationship("Order", back_populates="status_history")

    def __repr__(self):
        return f"<OrderStatusHistory {self.from_status} -> {self.to_status}>"
