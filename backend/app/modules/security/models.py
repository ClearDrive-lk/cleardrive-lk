# backend/app/modules/security/models.py

from __future__ import annotations

import datetime as dt
from uuid import UUID as PyUUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column
import enum
from app.core.database import Base
from app.core.models import TimestampMixin, UUIDMixin, GUID, IPAddress


class VerificationStatus(str, enum.Enum):
    """File integrity verification status."""

    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    TAMPERED = "TAMPERED"


class SecurityEventType(str, enum.Enum):
    """Security event types."""

    AUTH_FAILURE = "AUTH_FAILURE"
    TOKEN_REUSE = "TOKEN_REUSE"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    IMPOSSIBLE_TRAVEL = "IMPOSSIBLE_TRAVEL"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    PAYMENT_MANIPULATION = "PAYMENT_MANIPULATION"
    FILE_TAMPERING = "FILE_TAMPERING"
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    ACCOUNT_LOCKOUT = "ACCOUNT_LOCKOUT"


class Severity(str, enum.Enum):
    """Security event severity."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class UserTier(str, enum.Enum):
    """User reputation tier."""

    SUSPICIOUS = "SUSPICIOUS"
    STANDARD = "STANDARD"
    TRUSTED = "TRUSTED"
    PREMIUM = "PREMIUM"


class FileIntegrity(Base, UUIDMixin, TimestampMixin):
    """File integrity monitoring - SHA-256 checksums."""

    __tablename__ = "file_integrity"

    # File info
    file_url: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100))

    # Upload tracking
    uploaded_by: Mapped[PyUUID | None] = mapped_column(GUID(), ForeignKey("users.id"))

    # Verification
    last_verified: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    verification_status: Mapped[VerificationStatus] = mapped_column(
        SQLEnum(VerificationStatus), default=VerificationStatus.PENDING, nullable=False, index=True
    )

    def __repr__(self):
        return f"<FileIntegrity {self.file_url} - {self.verification_status}>"


class SecurityEvent(Base, UUIDMixin, TimestampMixin):
    """Security event logging."""

    __tablename__ = "security_events"

    # Event info
    event_type: Mapped[SecurityEventType] = mapped_column(
        SQLEnum(SecurityEventType), nullable=False, index=True
    )
    severity: Mapped[Severity] = mapped_column(SQLEnum(Severity), nullable=False, index=True)

    # User & source
    user_id: Mapped[PyUUID | None] = mapped_column(
        GUID(), ForeignKey("users.id"), index=True
    )
    ip_address: Mapped[str | None] = mapped_column(IPAddress())
    user_agent: Mapped[str | None] = mapped_column(Text)
    country_code: Mapped[str | None] = mapped_column(String(2))

    # Details
    details: Mapped[dict | None] = mapped_column(JSON)

    # Resolution
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_by: Mapped[PyUUID | None] = mapped_column(GUID(), ForeignKey("users.id"))
    resolved_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self):
        return f"<SecurityEvent {self.event_type} - {self.severity}>"


class UserReputation(Base):
    """User reputation and trust scoring."""

    __tablename__ = "user_reputation"

    user_id: Mapped[PyUUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )

    # Trust score (0-100)
    trust_score: Mapped[int] = mapped_column(Integer, default=50, nullable=False)

    # Counters
    successful_orders: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_payments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    kyc_rejections: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    security_alerts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Tier
    current_tier: Mapped[UserTier] = mapped_column(
        SQLEnum(UserTier), default=UserTier.STANDARD, nullable=False, index=True
    )

    # Behavior flags
    impossible_travel_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    multiple_devices_flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamp
    last_updated: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self):
        return f"<UserReputation {self.user_id} - {self.current_tier}>"


class RateLimitViolation(Base, UUIDMixin):
    """Rate limit violation tracking."""

    __tablename__ = "rate_limit_violations"

    # User & source
    user_id: Mapped[PyUUID | None] = mapped_column(
        GUID(), ForeignKey("users.id"), index=True
    )
    ip_address: Mapped[str] = mapped_column(IPAddress(), nullable=False, index=True)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)

    # Violation details
    limit_tier: Mapped[str | None] = mapped_column(String(20))
    requests_attempted: Mapped[int | None] = mapped_column(Integer)
    limit_exceeded: Mapped[int | None] = mapped_column(Integer)

    # Timestamp
    violation_time: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self):
        return f"<RateLimitViolation {self.ip_address} - {self.endpoint}>"
