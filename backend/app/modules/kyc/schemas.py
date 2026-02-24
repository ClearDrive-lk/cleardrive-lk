# backend/app/modules/kyc/schemas.py

"""
KYC Pydantic schemas.
Author: Pavara
Story: CD-50
"""

from datetime import date, datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


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
    extracted_data: Optional[Dict[str, Any]]
    created_at: datetime


class KYCStatusResponse(BaseModel):
    """Response for KYC status check."""

    has_kyc: bool
    status: Optional[str]
    submitted_at: Optional[datetime]
    reviewed_at: Optional[datetime]
    rejection_reason: Optional[str]
    nic_number: Optional[str]
    full_name: Optional[str]
