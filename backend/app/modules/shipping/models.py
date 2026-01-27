# backend/app/modules/shipping/models.py

from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Integer, Boolean, Enum as SQLEnum, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.core.database import Base
from app.core.models import TimestampMixin, UUIDMixin


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
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    exporter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Shipping information
    vessel_name = Column(String(255))
    voyage_number = Column(String(100))
    departure_port = Column(String(255))
    arrival_port = Column(String(255), default="Colombo, Sri Lanka")
    
    # Dates
    departure_date = Column(Date)
    estimated_arrival_date = Column(Date)
    actual_arrival_date = Column(Date)
    
    # Tracking
    container_number = Column(String(100))
    seal_number = Column(String(100))
    tracking_number = Column(String(255))
    
    # Status
    status = Column(SQLEnum(ShipmentStatus), default=ShipmentStatus.PENDING_SHIPMENT, nullable=False, index=True)
    
    # Submission & Approval
    submitted_at = Column(DateTime(timezone=True))
    admin_approved_at = Column(DateTime(timezone=True))
    admin_approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    order = relationship("Order", back_populates="shipment_details")
    documents = relationship("ShippingDocument", back_populates="shipment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ShipmentDetails {self.order_id} - {self.vessel_name}>"


class ShippingDocument(Base, UUIDMixin, TimestampMixin):
    """Shipping document model - exporter uploaded docs."""
    
    __tablename__ = "shipping_documents"
    
    shipment_id = Column(UUID(as_uuid=True), ForeignKey("shipment_details.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Document info
    document_type = Column(SQLEnum(DocumentType), nullable=False, index=True)
    file_url = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    
    # Upload info
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Admin verification
    verified = Column(Boolean, default=False, nullable=False)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    verified_at = Column(DateTime(timezone=True))
    
    # Relationships
    shipment = relationship("ShipmentDetails", back_populates="documents")
    
    def __repr__(self):
        return f"<ShippingDocument {self.document_type} - {self.file_name}>"