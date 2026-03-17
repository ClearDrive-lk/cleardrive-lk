"""Shipping Pydantic schemas.

Author: Kalidu
Story: CD-70
"""

import re
from datetime import date, datetime
from enum import Enum
from typing import Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


# ============== ENUMS ==============
class DocumentType(str, Enum):
    """Shipping document types."""

    BILL_OF_LADING = "BILL_OF_LADING"
    BILL_OF_LANDING = "BILL_OF_LANDING"
    COMMERCIAL_INVOICE = "COMMERCIAL_INVOICE"
    PACKING_LIST = "PACKING_LIST"
    EXPORT_CERTIFICATE = "EXPORT_CERTIFICATE"
    INSURANCE_CERTIFICATE = "INSURANCE_CERTIFICATE"
    CERTIFICATE_OF_ORIGIN = "CERTIFICATE_OF_ORIGIN"
    CONTAINER_PHOTO = "CONTAINER_PHOTO"
    OTHER = "OTHER"


# ============== SHIPMENT SCHEMAS ==============
class ShippingDetailsSubmit(BaseModel):
    """Schema for submitting shipping details (CD-71)."""

    vessel_name: str = Field(min_length=3, max_length=255)
    vessel_registration: str = Field(min_length=3, max_length=100)
    voyage_number: str = Field(min_length=1, max_length=100)
    departure_port: str = Field(min_length=3, max_length=255)
    arrival_port: str = Field(min_length=3, max_length=255)
    departure_date: date
    estimated_arrival_date: date
    container_number: str = Field(min_length=5, max_length=100)
    bill_of_landing_number: str = Field(min_length=5, max_length=100)
    seal_number: str = Field(min_length=2, max_length=100)
    tracking_number: str = Field(min_length=2, max_length=255)

    @field_validator(
        "vessel_name",
        "vessel_registration",
        "voyage_number",
        "departure_port",
        "arrival_port",
        "container_number",
        "bill_of_landing_number",
        "seal_number",
        "tracking_number",
        mode="before",
    )
    @classmethod
    def _trim_required_strings(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty")
        return cleaned

    @field_validator("container_number", mode="after")
    @classmethod
    def _validate_container_number(cls, value: str) -> str:
        normalized = value.replace(" ", "").upper()
        if not re.match(r"^[A-Z0-9-]{5,100}$", normalized):
            raise ValueError("Invalid container number format")
        return normalized

    @field_validator("bill_of_landing_number", mode="after")
    @classmethod
    def _validate_bill_of_landing_number(cls, value: str) -> str:
        normalized = value.replace(" ", "").upper()
        if not re.match(r"^[A-Z0-9-]{5,100}$", normalized):
            raise ValueError("Invalid bill of landing number format")
        return normalized

    @model_validator(mode="after")
    def _validate_dates_and_ports(self):
        if self.estimated_arrival_date <= self.departure_date:
            raise ValueError("Estimated arrival date must be after departure date")
        if self.departure_port.lower() == self.arrival_port.lower():
            raise ValueError("Departure and arrival ports must be different")
        return self


class ShippingDetailsResponse(BaseModel):
    """Response schema for shipment details."""

    id: UUID
    order_id: UUID

    exporter_id: Optional[UUID] = None
    assigned_exporter_id: Optional[UUID] = None  # Alias for backward compatibility
    vessel_name: Optional[str] = None
    vessel_registration: Optional[str] = None
    voyage_number: Optional[str] = None
    departure_port: Optional[str] = None
    arrival_port: Optional[str] = None
    departure_date: Optional[date] = None
    estimated_departure_date: Optional[date] = None
    actual_departure_date: Optional[date] = None
    estimated_arrival_date: Optional[date] = None
    actual_arrival_date: Optional[date] = None
    container_number: Optional[str] = None
    bill_of_landing_number: Optional[str] = None
    seal_number: Optional[str] = None
    tracking_number: Optional[str] = None
    documents_uploaded: bool = False
    approved: bool = False
    status: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ShipmentDetailsResponse(ShippingDetailsResponse):
    """Backward-compatible alias for CD-70 naming."""


class AssignableOrderItem(BaseModel):
    """Admin list item for orders eligible for exporter assignment."""

    id: UUID
    user_id: UUID
    vehicle_id: UUID
    customer_name: str
    customer_email: str
    vehicle_label: str
    status: str
    payment_status: str
    total_cost_lkr: float | None = None
    created_at: datetime

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
