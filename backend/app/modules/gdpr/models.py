# backend/app/modules/gdpr/models.py

from __future__ import annotations

import datetime as dt
from uuid import UUID as PyUUID

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.core.database import Base
from app.core.models import TimestampMixin, UUIDMixin
from sqlalchemy.orm import Mapped, mapped_column


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

    user_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Request info
    request_type: Mapped[RequestType] = mapped_column(SQLEnum(RequestType), nullable=False)
    status: Mapped[RequestStatus] = mapped_column(
        SQLEnum(RequestStatus), default=RequestStatus.PENDING, nullable=False, index=True
    )

    # Timestamps
    requested_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))

    # Export data
    export_file_url: Mapped[str | None] = mapped_column(Text)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text)

    def __repr__(self):
        return f"<GDPRRequest {self.request_type} - {self.status}>"
