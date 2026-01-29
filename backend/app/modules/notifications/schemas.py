# backend/app/modules/notifications/schemas.py

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class EmailPriority(str, Enum):
    """Email priority levels"""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class EmailTemplate(str, Enum):
    """Available email templates"""
    OTP = "otp"
    ORDER_CONFIRMATION = "order_confirmation"
    PAYMENT_CONFIRMATION = "payment_confirmation"
    KYC_APPROVAL = "kyc_approval"
    KYC_REJECTION = "kyc_rejection"
    SHIPMENT_NOTIFICATION = "shipment_notification"
    STATUS_UPDATE = "status_update"
    WELCOME = "welcome"
    PASSWORD_RESET = "password_reset"


class EmailRequest(BaseModel):
    """Request to send an email"""
    recipient_email: EmailStr
    recipient_name: Optional[str] = None
    subject: str = Field(..., min_length=1, max_length=500)
    template: EmailTemplate
    template_data: Dict[str, Any] = Field(default_factory=dict)
    priority: EmailPriority = EmailPriority.NORMAL
    
    @field_validator('template_data')
    @classmethod
    def validate_template_data(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure template_data doesn't contain sensitive info in keys"""
        sensitive_keys = ['password', 'secret', 'token', 'api_key']
        for key in v.keys():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                raise ValueError(f"Sensitive key '{key}' not allowed in template_data")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "recipient_email": "user@example.com",
                "recipient_name": "John Doe",
                "subject": "Your OTP Code",
                "template": "otp",
                "template_data": {
                    "otp_code": "123456",
                    "expires_in_minutes": 5
                },
                "priority": "HIGH"
            }
        }


class EmailResponse(BaseModel):
    """Response after sending email"""
    success: bool
    message: str
    email_log_id: Optional[int] = None
    queued: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Email queued successfully",
                "email_log_id": 123,
                "queued": True
            }
        }


class EmailLogResponse(BaseModel):
    """Email log response"""
    id: int
    recipient_email: str
    recipient_name: Optional[str]
    subject: str
    template_name: str
    status: str
    attempts: int
    max_attempts: int
    error_message: Optional[str]
    sent_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EmailQueueStats(BaseModel):
    """Email queue statistics"""
    total_pending: int
    total_queued: int
    total_sending: int
    total_failed: int
    total_sent_today: int
    queue_size: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_pending": 5,
                "total_queued": 12,
                "total_sending": 2,
                "total_failed": 3,
                "total_sent_today": 145,
                "queue_size": 17
            }
        }


class BulkEmailRequest(BaseModel):
    """Request to send bulk emails (admin only)"""
    recipients: list[EmailStr] = Field(..., min_length=1, max_length=100)
    subject: str = Field(..., min_length=1, max_length=500)
    template: EmailTemplate
    template_data: Dict[str, Any] = Field(default_factory=dict)
    priority: EmailPriority = EmailPriority.NORMAL
    
    @field_validator('recipients')
    @classmethod
    def validate_recipients(cls, v: list[EmailStr]) -> list[EmailStr]:
        """Remove duplicates"""
        return list(set(v))


class BulkEmailResponse(BaseModel):
    """Response for bulk email sending"""
    total_queued: int
    email_log_ids: list[int]
    failed: int = 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_queued": 50,
                "email_log_ids": [1, 2, 3],
                "failed": 0
            }
        }
