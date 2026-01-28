# backend/app/modules/auth/models.py

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, Enum as SQLEnum,func

from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, INET
import enum
from app.core.database import Base
from app.core.models import TimestampMixin, UUIDMixin


class Role(str, enum.Enum):
    """User roles enum."""
    CUSTOMER = "CUSTOMER"
    ADMIN = "ADMIN"
    CLEARING_AGENT = "CLEARING_AGENT"
    FINANCE_PARTNER = "FINANCE_PARTNER"
    EXPORTER = "EXPORTER"


class User(Base, UUIDMixin, TimestampMixin):
    """User model - all authenticated users."""
    
    __tablename__ = "users"
    
    # Basic info
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    phone = Column(String(20))
    
    # Authentication
    google_id = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255))  # For admin backup password
    
    # Role & Status
    role = Column(SQLEnum(Role), default=Role.CUSTOMER, nullable=False, index=True)
    
    # Security tracking
    failed_auth_attempts = Column(Integer, default=0, nullable=False)
    last_failed_auth = Column(DateTime(timezone=True))
    
    # GDPR
    deleted_at = Column(DateTime(timezone=True), index=True)

    # Reviewed KYC Documents
    reviewed_kyc_documents = relationship(
        "KYCDocument",
        foreign_keys="[KYCDocument.reviewed_by]",
        back_populates="reviewed_by_user",
    )
    
    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    kyc_document = relationship("KYCDocument", back_populates="user", foreign_keys="[KYCDocument.user_id]", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.email}>"


class Session(Base, UUIDMixin, TimestampMixin):
    """User session tracking."""
    
    __tablename__ = "sessions"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Session metadata
    refresh_token_hash = Column(String(255), nullable=False)
    ip_address = Column(INET)
    user_agent = Column(String(500))
    device_info = Column(String(255))
    location = Column(String(255))  # City, Country
    
    # Session status
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_active = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        return f"<Session {self.user_id}>"