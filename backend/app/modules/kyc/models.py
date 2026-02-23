# backend/app/modules/kyc/models.py

from __future__ import annotations

import datetime as dt
import enum
from typing import TYPE_CHECKING
from uuid import UUID as PyUUID

from app.core.database import Base
from app.core.models import GUID, TimestampMixin, UUIDMixin
from sqlalchemy import JSON, Date, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.modules.auth.models import User


class KYCStatus(str, enum.Enum):
    """KYC verification status."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class KYCDocument(Base, UUIDMixin, TimestampMixin):
    """KYC document model - user verification."""

    __tablename__ = "kyc_documents"

    user_id: Mapped[PyUUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Personal info (encrypted)
    nic_number: Mapped[str | None] = mapped_column(String(255))  # Encrypted
    full_name: Mapped[str | None] = mapped_column(String(255))
    date_of_birth: Mapped[dt.date | None] = mapped_column(Date)
    address: Mapped[str | None] = mapped_column(Text)  # Encrypted
    gender: Mapped[str | None] = mapped_column(String(10))

    # Document URLs
    nic_front_url: Mapped[str] = mapped_column(Text, nullable=False)
    nic_back_url: Mapped[str] = mapped_column(Text, nullable=False)
    selfie_url: Mapped[str] = mapped_column(Text, nullable=False)

    # AI extraction results
    extracted_data: Mapped[dict | None] = mapped_column(JSON)  # Claude API extracted data
    discrepancies: Mapped[dict | None] = mapped_column(
        JSON
    )  # Differences between extracted and provided data

    # Status
    status: Mapped[KYCStatus] = mapped_column(
        SQLEnum(KYCStatus), default=KYCStatus.PENDING, nullable=False, index=True
    )

    # Review
    reviewed_by: Mapped[PyUUID | None] = mapped_column(GUID(), ForeignKey("users.id"))
    reviewed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text)

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="kyc_document", foreign_keys=[user_id])
    reviewed_by_user: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[reviewed_by],
        viewonly=True,
        back_populates="reviewed_kyc_documents",
    )

    def __repr__(self):
        return f"<KYCDocument {self.user_id} - {self.status}>"
