# backend/app/modules/gdpr/models.py

from __future__ import annotations

import datetime as dt
import enum
from typing import TYPE_CHECKING
from uuid import UUID as PyUUID

from app.core.database import Base
from app.core.models import GUID, TimestampMixin, UUIDMixin
from sqlalchemy import Boolean, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.modules.auth.models import User


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
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Request info
    request_type: Mapped[RequestType] = mapped_column(SQLEnum(RequestType), nullable=False)
    status: Mapped[RequestStatus] = mapped_column(
        SQLEnum(RequestStatus),
        default=RequestStatus.PENDING,
        nullable=False,
        index=True,
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


class GDPRDeletionStatus(str, enum.Enum):
    """Status lifecycle for GDPR deletion processing."""

    REQUESTED = "REQUESTED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class GDPRDeletion(Base, UUIDMixin):
    """Track GDPR account deletion requests and processing outcomes."""

    __tablename__ = "gdpr_deletions"

    user_id: Mapped[PyUUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    requested_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    processed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))

    status: Mapped[GDPRDeletionStatus] = mapped_column(
        SQLEnum(GDPRDeletionStatus),
        default=GDPRDeletionStatus.REQUESTED,
        nullable=False,
        index=True,
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text)

    data_anonymized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    kyc_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sessions_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))

    original_email: Mapped[str | None] = mapped_column(String(255))
    original_name: Mapped[str | None] = mapped_column(String(255))

    user: Mapped["User"] = relationship("User", viewonly=True)

    def __repr__(self):
        return f"<GDPRDeletion {self.user_id} - {self.status}>"
