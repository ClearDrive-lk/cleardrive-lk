# backend/app/modules/security/models.py

from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    Boolean,
    Enum as SQLEnum,
    Text,
    func,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
import enum
from app.core.database import Base
from app.core.models import TimestampMixin, UUIDMixin


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
    file_url = Column(String(500), unique=True, nullable=False, index=True)
    sha256_hash = Column(String(64), nullable=False, index=True)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100))

    # Upload tracking
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Verification
    last_verified = Column(DateTime(timezone=True))
    verification_status = Column(
        SQLEnum(VerificationStatus), default=VerificationStatus.PENDING, nullable=False, index=True
    )

    def __repr__(self):
        return f"<FileIntegrity {self.file_url} - {self.verification_status}>"


class SecurityEvent(Base, UUIDMixin, TimestampMixin):
    """Security event logging."""

    __tablename__ = "security_events"

    # Event info
    event_type = Column(SQLEnum(SecurityEventType), nullable=False, index=True)
    severity = Column(SQLEnum(Severity), nullable=False, index=True)

    # User & source
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    ip_address = Column(INET)
    user_agent = Column(Text)
    country_code = Column(String(2))

    # Details
    details = Column(JSONB)

    # Resolution
    resolved = Column(Boolean, default=False, nullable=False)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    resolved_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<SecurityEvent {self.event_type} - {self.severity}>"


class UserReputation(Base):
    """User reputation and trust scoring."""

    __tablename__ = "user_reputation"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )

    # Trust score (0-100)
    trust_score = Column(Integer, default=50, nullable=False)

    # Counters
    successful_orders = Column(Integer, default=0, nullable=False)
    failed_payments = Column(Integer, default=0, nullable=False)
    kyc_rejections = Column(Integer, default=0, nullable=False)
    security_alerts = Column(Integer, default=0, nullable=False)

    # Tier
    current_tier = Column(SQLEnum(UserTier), default=UserTier.STANDARD, nullable=False, index=True)

    # Behavior flags
    impossible_travel_detected = Column(Boolean, default=False, nullable=False)
    multiple_devices_flagged = Column(Boolean, default=False, nullable=False)

    # Timestamp
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self):
        return f"<UserReputation {self.user_id} - {self.current_tier}>"


class RateLimitViolation(Base, UUIDMixin):
    """Rate limit violation tracking."""

    __tablename__ = "rate_limit_violations"

    # User & source
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    ip_address = Column(INET, nullable=False, index=True)
    endpoint = Column(String(255), nullable=False)

    # Violation details
    limit_tier = Column(String(20))
    requests_attempted = Column(Integer)
    limit_exceeded = Column(Integer)

    # Timestamp
    violation_time = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self):
        return f"<RateLimitViolation {self.ip_address} - {self.endpoint}>"
