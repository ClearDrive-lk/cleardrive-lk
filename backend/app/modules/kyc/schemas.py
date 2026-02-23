# backend/app/modules/kyc/schemas.py

"""KYC Pydantic schemas."""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class KYCUploadResponse(BaseModel):
    """Response after KYC document upload."""

    id: UUID
    user_id: UUID
    nic_number: str | None
    full_name: str | None
    date_of_birth: date | None
    address: str | None
    gender: str | None
    status: str
    nic_front_url: str
    nic_back_url: str
    selfie_url: str
    extracted_data: dict[str, Any] | None
    created_at: datetime

    class Config:
        from_attributes = True


class KYCStatusResponse(BaseModel):
    """Response for KYC status check."""

    has_kyc: bool
    status: str | None
    submitted_at: datetime | None
    reviewed_at: datetime | None
    rejection_reason: str | None
    nic_number: str | None
    full_name: str | None
