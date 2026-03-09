# backend/app/modules/kyc/schemas.py

"""
KYC Pydantic schemas.
Author: Pavara
Story: CD-50
"""

from datetime import date, datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class KYCUploadResponse(BaseModel):
    """Response after KYC document upload."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    nic_number: Optional[str]
    full_name: Optional[str]
    date_of_birth: Optional[date]
    address: Optional[str]
    gender: Optional[str]
    status: str
    nic_front_url: str
    nic_back_url: str
    selfie_url: str
    user_provided_data: Optional[Dict[str, Any]]
    extracted_data: Optional[Dict[str, Any]]
    created_at: datetime


class KYCUploadResultResponse(BaseModel):
    """Guide-aligned response for KYC upload endpoint."""

    message: str
    kyc_id: str
    status: str
    extraction_success: bool
    needs_manual_review: bool


class KYCUserProvidedData(BaseModel):
    """User-entered KYC identity fields submitted with the upload."""

    nic_number: Optional[str] = None
    full_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    gender: Optional[str] = None


class KYCStatusResponse(BaseModel):
    """Response for KYC status check."""

    has_kyc: bool
    status: Optional[str]
    submitted_at: Optional[datetime]
    reviewed_at: Optional[datetime]
    rejection_reason: Optional[str]
    nic_number: Optional[str]
    full_name: Optional[str]


class KYCAdminComparisonField(BaseModel):
    """Single field comparison between extracted and stored values."""

    label: str
    extracted_value: Optional[str]
    user_value: Optional[str]
    matches: bool


class KYCAdminPendingItem(BaseModel):
    """Admin queue item for KYC review."""

    id: UUID
    user_id: UUID
    user_email: str
    user_name: str
    status: str
    created_at: datetime
    extraction_method: str
    auto_extracted: bool
    needs_manual_extraction: bool


class KYCAdminDetailResponse(BaseModel):
    """Detailed admin KYC review payload."""

    id: UUID
    user_id: UUID
    user_email: str
    user_name: str
    status: str
    created_at: datetime
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[UUID]
    rejection_reason: Optional[str]
    nic_front_url: str
    nic_back_url: str
    selfie_url: str
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    user_provided_data: Dict[str, Optional[str]] = Field(default_factory=dict)
    discrepancies: Dict[str, bool] = Field(default_factory=dict)
    comparison_rows: list[KYCAdminComparisonField] = Field(default_factory=list)
    extraction_method: str
    auto_extracted: bool
    needs_manual_extraction: bool


class KYCRejectRequest(BaseModel):
    """Reject request for admin KYC review."""

    reason: str = Field(..., min_length=10)
