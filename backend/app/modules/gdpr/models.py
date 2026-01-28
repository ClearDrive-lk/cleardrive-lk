# backend/app/modules/gdpr/models.py

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum as SQLEnum, func
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.core.database import Base
from app.core.models import TimestampMixin, UUIDMixin


class RequestType(str, enum.Enum):
    """GDPR request types."""

    DATA_EXPORT = "DATA_EXPORT"
    DATA_DELETION = "DATA_DELETION"
    DATA_RECTIFICATION = "DATA_RECTIFICATION"


class RequestStatus(str, enum.Enum):
    """GDPR request status."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class GDPRRequest(Base, UUIDMixin, TimestampMixin):
    """GDPR compliance requests."""

    __tablename__ = "gdpr_requests"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Request info
    request_type = Column(SQLEnum(RequestType), nullable=False)
    status = Column(
        SQLEnum(RequestStatus), default=RequestStatus.PENDING, nullable=False, index=True
    )

    # Timestamps
    requested_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True))

    # Export data
    export_file_url = Column(Text)

    # Notes
    notes = Column(Text)

    def __repr__(self):
        return f"<GDPRRequest {self.request_type} - {self.status}>"
