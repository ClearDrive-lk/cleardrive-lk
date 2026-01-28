# backend/app/modules/auth/models.py

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING
from uuid import UUID as PyUUID

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, func

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, INET
import enum
from app.core.database import Base
from app.core.models import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.modules.kyc.models import KYCDocument
    from app.modules.orders.models import Order


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
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(20))

    # Authentication
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))  # For admin backup password

    # Role & Status
    role: Mapped[Role] = mapped_column(
        SQLEnum(Role), default=Role.CUSTOMER, nullable=False, index=True
    )

    # Security tracking
    failed_auth_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_failed_auth: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))

    # GDPR
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    # Reviewed KYC Documents
    reviewed_kyc_documents = relationship(
        "KYCDocument",
        foreign_keys="[KYCDocument.reviewed_by]",
        back_populates="reviewed_by_user",
    )

    # Relationships
    sessions: Mapped[list[Session]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
    orders: Mapped[list[Order]] = relationship(
        "Order", back_populates="user", cascade="all, delete-orphan"
    )
    kyc_document: Mapped[KYCDocument | None] = relationship(
        "KYCDocument",
        back_populates="user",
        foreign_keys="[KYCDocument.user_id]",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<User {self.email}>"


class Session(Base, UUIDMixin, TimestampMixin):
    """User session tracking."""

    __tablename__ = "sessions"

    user_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Session metadata
    refresh_token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(String(500))
    device_info: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255))  # City, Country

    # Session status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_active: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<Session {self.user_id}>"
