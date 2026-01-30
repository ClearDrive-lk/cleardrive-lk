# backend/app/modules/shipping/models.py

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, Date, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.core.database import Base
from app.core.models import TimestampMixin, UUIDMixin, GUID

if TYPE_CHECKING:
    from app.modules.orders.models import Order


class ShipmentStatus(str, enum.Enum):
    """Shipment status enum."""

    PENDING_SHIPMENT = "PENDING_SHIPMENT"
    DOCS_UPLOADED = "DOCS_UPLOADED"
    AWAITING_ADMIN_APPROVAL = "AWAITING_ADMIN_APPROVAL"
    CONFIRMED_SHIPPED = "CONFIRMED_SHIPPED"


class DocumentType(str, enum.Enum):
    """Shipping document types."""

    BILL_OF_LADING = "BILL_OF_LADING"
    PACKING_LIST = "PACKING_LIST"
    EXPORT_CERTIFICATE = "EXPORT_CERTIFICATE"
    COMMERCIAL_INVOICE = "COMMERCIAL_INVOICE"
    INSURANCE_CERTIFICATE = "INSURANCE_CERTIFICATE"


class ShipmentDetails(Base, UUIDMixin, TimestampMixin):
    """Shipment details model - exporter shipment info."""

    __tablename__ = "shipment_details"

    # References
    order_id: Mapped[PyUUID] = mapped_column(
        GUID(),
        ForeignKey("orders.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    exporter_id: Mapped[PyUUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False, index=True
    )

    # Shipping information
    vessel_name: Mapped[str | None] = mapped_column(String(255))
    voyage_number: Mapped[str | None] = mapped_column(String(100))
    departure_port: Mapped[str | None] = mapped_column(String(255))
    arrival_port: Mapped[str | None] = mapped_column(String(255), default="Colombo, Sri Lanka")

    # Dates
    departure_date: Mapped[dt.date | None] = mapped_column(Date)
    estimated_arrival_date: Mapped[dt.date | None] = mapped_column(Date)
    actual_arrival_date: Mapped[dt.date | None] = mapped_column(Date)

    # Tracking
    container_number: Mapped[str | None] = mapped_column(String(100))
    seal_number: Mapped[str | None] = mapped_column(String(100))
    tracking_number: Mapped[str | None] = mapped_column(String(255))

    # Status
    status: Mapped[ShipmentStatus] = mapped_column(
        SQLEnum(ShipmentStatus), default=ShipmentStatus.PENDING_SHIPMENT, nullable=False, index=True
    )

    # Submission & Approval
    submitted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    admin_approved_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    admin_approved_by: Mapped[PyUUID | None] = mapped_column(
        GUID(), ForeignKey("users.id")
    )

    # Relationships
    order: Mapped[Order] = relationship("Order", back_populates="shipment_details")
    documents: Mapped[list[ShippingDocument]] = relationship(
        "ShippingDocument", back_populates="shipment", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ShipmentDetails {self.order_id} - {self.vessel_name}>"


class ShippingDocument(Base, UUIDMixin, TimestampMixin):
    """Shipping document model - exporter uploaded docs."""

    __tablename__ = "shipping_documents"

    shipment_id: Mapped[PyUUID] = mapped_column(
        GUID(),
        ForeignKey("shipment_details.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Document info
    document_type: Mapped[DocumentType] = mapped_column(
        SQLEnum(DocumentType), nullable=False, index=True
    )
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int | None] = mapped_column(Integer)
    mime_type: Mapped[str | None] = mapped_column(String(100))

    # Upload info
    uploaded_by: Mapped[PyUUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    uploaded_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Admin verification
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_by: Mapped[PyUUID | None] = mapped_column(GUID(), ForeignKey("users.id"))
    verified_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    shipment: Mapped[ShipmentDetails] = relationship("ShipmentDetails", back_populates="documents")

    def __repr__(self):
        return f"<ShippingDocument {self.document_type} - {self.file_name}>"
