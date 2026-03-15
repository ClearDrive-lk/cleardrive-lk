"""
Audit log model for tracking admin actions.
"""

import enum
import uuid
from datetime import datetime
from typing import Any
from uuid import UUID as PyUUID

from app.core.database import Base
from app.core.models import GUID
from sqlalchemy import JSON, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column


class AuditEventType(str, enum.Enum):
    """Types of audit events."""

    ROLE_CHANGED = "ROLE_CHANGED"
    USER_CREATED = "USER_CREATED"
    USER_DELETED = "USER_DELETED"
    USER_SUSPENDED = "USER_SUSPENDED"
    USER_ACTIVATED = "USER_ACTIVATED"
    KYC_APPROVED = "KYC_APPROVED"
    KYC_REJECTED = "KYC_REJECTED"
    KYC_AUTO_EXTRACTION_FAILED = "KYC_AUTO_EXTRACTION_FAILED"
    KYC_MANUAL_REVIEW_QUEUED = "KYC_MANUAL_REVIEW_QUEUED"
    GAZETTE_UPLOADED = "GAZETTE_UPLOADED"
    GAZETTE_APPROVED = "GAZETTE_APPROVED"
    GAZETTE_REJECTED = "GAZETTE_REJECTED"
    TAX_RULES_ACTIVATED = "TAX_RULES_ACTIVATED"
    TAX_RULES_DEACTIVATED = "TAX_RULES_DEACTIVATED"
    ORDER_STATUS_CHANGED = "ORDER_STATUS_CHANGED"
    PAYMENT_PROCESSED = "PAYMENT_PROCESSED"
    REFUND_ISSUED = "REFUND_ISSUED"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"  # pragma: allowlist secret
    USER_TIER_DOWNGRADED = "USER_TIER_DOWNGRADED"
    USER_TIER_UPGRADED = "USER_TIER_UPGRADED"


class AuditLog(Base):
    """Audit log for tracking admin actions."""

    __tablename__ = "audit_logs"

    id: Mapped[PyUUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    event_type: Mapped[AuditEventType] = mapped_column(
        Enum(AuditEventType), nullable=False, index=True
    )
    user_id: Mapped[PyUUID | None] = mapped_column(GUID(), nullable=True, index=True)
    admin_id: Mapped[PyUUID | None] = mapped_column(GUID(), nullable=True, index=True)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
