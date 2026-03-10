"""
Email delivery logs.
Author: Parindra gallage
Story: CD-120.5
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class EmailStatus(str, enum.Enum):
    """Email delivery status."""
    QUEUED = "QUEUED"
    SENDING = "SENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    BOUNCED = "BOUNCED"


class EmailLog(Base):
    """
    Email delivery logs.
    
    Story: CD-120.5
    
    Tracks every email sent through the system.
    """
    
    __tablename__ = "email_logs"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Email Details
    to_email = Column(String(255), nullable=False)
    from_email = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    
    # Template
    template_name = Column(String(100), nullable=True)
    template_data = Column(JSON, nullable=True)
    
    # Content
    html_body = Column(Text, nullable=True)
    text_body = Column(Text, nullable=True)
    
    # Status
    status = Column(SQLEnum(EmailStatus), default=EmailStatus.QUEUED)
    
    # Delivery
    sent_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Retry
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    next_retry_at = Column(DateTime, nullable=True)
    
    # Metadata
    user_id = Column(UUID(as_uuid=True), nullable=True)
    order_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<EmailLog {self.to_email} - {self.status.value}>"
