# backend/app/modules/payments/schemas.py

"""
Payment Pydantic schemas.
Author: Tharin
Epic: CD-E5
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PaymentInitiate(BaseModel):
    """Schema for initiating payment."""

    order_id: UUID
    idempotency_key: Optional[str] = Field(default=None, min_length=16, max_length=255)


class PaymentOTPRequest(BaseModel):
    """Request a payment verification OTP for an order."""

    order_id: UUID


class PaymentOTPRequestResponse(BaseModel):
    """Payment OTP request response."""

    message: str
    expires_in_seconds: int
    otp: Optional[str] = None


class PaymentOTPVerify(BaseModel):
    """Verify a payment verification OTP for an order."""

    order_id: UUID
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP")


class PaymentOTPVerifyResponse(BaseModel):
    """Payment OTP verification response."""

    verified: bool
    message: str


class PaymentInitiateResponse(BaseModel):
    """Response after payment initiation."""

    payment_id: UUID
    payment_url: str
    payhere_params: Dict[str, str]
    payhere_url: str
    amount: Decimal
    currency: str
    order_id: UUID


class PaymentWebhook(BaseModel):
    """PayHere webhook data."""

    merchant_id: str
    order_id: str
    payhere_amount: str
    payhere_currency: str
    status_code: str
    md5sig: str

    # Optional fields
    payment_id: Optional[str] = None
    method: Optional[str] = None
    card_holder_name: Optional[str] = None
    card_no: Optional[str] = None


class PaymentResponse(BaseModel):
    """Payment response."""

    id: UUID
    order_id: UUID
    amount: Decimal
    currency: str
    status: str
    payhere_payment_id: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True
