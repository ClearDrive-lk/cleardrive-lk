# backend/app/modules/shipping/schemas.py

from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime, date
from uuid import UUID
from enum import Enum


# ============== ENUMS ==============
class DocumentType(str, Enum):
    """Shipping document types."""
    BILL_OF_LANDING = "BILL_OF_LANDING"
    PACKING_LIST = "PACKING_LIST"
    EXPORT_CERTIFICATE = "EXPORT_CERTIFICATE"
    COMMERCIAL_INVOICE = "COMMERCIAL_INVOICE"
    INSURANCE_CERTIFICATE = "INSURANCE_CERTIFICATE"


# ============== SHIPMENT SCHEMAS ==============
class ShippingDetailsSubmit(BaseModel):
    """Schema for submitting shipping details (CD-71)."""
    vessel_name: str
    voyage_number: str
    departure_port: str
    arrival_port: str
    departure_date: str  # ISO format date string
    estimated_arrival_date: str  # ISO format date string
    container_number: str
    seal_number: str
    tracking_number: str


class ShippingDetailsResponse(BaseModel):
    """Response schema for shipment details."""
    id: UUID
    order_id: UUID

    exporter_id: Optional[UUID] = None
    assigned_exporter_id: Optional[UUID] = None  # Alias for backward compatibility
    vessel_name: Optional[str] = None
    vessel_registration: Optional[str] = None
    departure_port: Optional[str] = None
    arrival_port: Optional[str] = None
    estimated_departure_date: Optional[date] = None
    actual_departure_date: Optional[date] = None
    estimated_arrival_date: Optional[date] = None
    actual_arrival_date: Optional[date] = None
    container_number: Optional[str] = None
    bill_of_landing_number: Optional[str] = None
    documents_uploaded: bool = False
    approved: bool = False
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============== DOCUMENT SCHEMAS ==============
class DocumentUploadResponse(BaseModel):
    """Response schema for document upload (CD-72)."""
    id: UUID
    shipment_id: UUID
    order_id: UUID
    document_type: str
    file_name: str
    file_size: int
    mime_type: str
    file_url: str
    verified: bool = False
    uploaded_at: datetime
    uploaded_by: UUID

    class Config:
        from_attributes = True


class DocumentListItem(BaseModel):
    """Schema for document list item."""
    id: UUID
    shipment_id: UUID
    order_id: UUID
    document_type: str
    file_name: str
    file_size: int
    mime_type: str
    file_url: str
    verified: bool = False
    uploaded_at: datetime
    uploaded_by: UUID

    class Config:
        from_attributes = True


class DocumentVerifyRequest(BaseModel):
    """Request schema for verifying/unverifying a document."""
    verified: bool


class RequiredDocumentsCheck(BaseModel):
    """Response schema for required documents check (CD-72.5)."""
    order_id: UUID
    total_required: int
    total_uploaded: int
    all_uploaded: bool
    uploaded_documents: list[str]
    missing_documents: list[str]
    completion_percentage: int


class DocumentStats(BaseModel):
    """Response schema for document statistics."""
    total_documents: int
    verified_documents: int
    pending_verification: int
    documents_by_type: Dict[str, int]


class ExporterAssignment(BaseModel):
    """Schema for assigning exporter to order."""
    exporter_id: UUID