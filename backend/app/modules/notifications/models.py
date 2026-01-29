# backend/app/modules/notifications/models.py

from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum, Boolean
from sqlalchemy.sql import func
from backend.app.core.database import Base
import enum


class EmailStatus(str, enum.Enum):
    """Email delivery status"""
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    SENDING = "SENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    RETRY = "RETRY"


class EmailLog(Base):
    """Track all email deliveries for audit and debugging"""
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Recipient info
    recipient_email = Column(String(255), nullable=False, index=True)
    recipient_name = Column(String(255), nullable=True)
    
    # Email details
    subject = Column(String(500), nullable=False)
    template_name = Column(String(100), nullable=False)  # e.g., 'otp', 'order_confirmation'
    
    # Status tracking
    status = Column(SQLEnum(EmailStatus), default=EmailStatus.PENDING, nullable=False, index=True)
    attempts = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=3, nullable=False)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata (DO NOT store actual email content - GDPR)
    template_data_summary = Column(Text, nullable=True)  # e.g., "OTP sent for login"
    
    # Success tracking
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<EmailLog(id={self.id}, to={self.recipient_email}, status={self.status})>"
    
    @property
    def can_retry(self) -> bool:
        """Check if email can be retried"""
        return self.attempts < self.max_attempts and self.status in [EmailStatus.FAILED, EmailStatus.RETRY]
    
    @property
    def is_final_state(self) -> bool:
        """Check if email is in final state"""
        return self.status in [EmailStatus.SENT] or (self.status == EmailStatus.FAILED and not self.can_retry)


# Index for efficient queries
from sqlalchemy import Index

Index('idx_email_status_created', EmailLog.status, EmailLog.created_at)
Index('idx_email_recipient_created', EmailLog.recipient_email, EmailLog.created_at)
"""SQLAlchemy models for notifications module"""