# backend/app/modules/kyc/models.py

from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Text, Enum as SQLEnum, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum
from app.core.database import Base
from app.core.models import TimestampMixin, UUIDMixin


class KYCStatus(str, enum.Enum):
    """KYC verification status."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class KYCDocument(Base, UUIDMixin, TimestampMixin):
    """KYC document model - user verification."""
    
    __tablename__ = "kyc_documents"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    # Personal info (encrypted)
    nic_number = Column(String(255), nullable=False)  # Encrypted
    full_name = Column(String(255), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    address = Column(Text, nullable=False)  # Encrypted
    
    # Document URLs
    nic_front_url = Column(Text, nullable=False)
    nic_back_url = Column(Text, nullable=False)
    selfie_url = Column(Text, nullable=False)
    
    # AI extraction results
    extracted_data = Column(JSONB)  # Claude API extracted data
    discrepancies = Column(JSONB)  # Differences between extracted and provided data
    
    # Status
    status = Column(SQLEnum(KYCStatus), default=KYCStatus.PENDING, nullable=False, index=True)
    
    # Review
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reviewed_at = Column(DateTime(timezone=True))
    rejection_reason = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="kyc_document", foreign_keys=[user_id])
    reviewed_by_user = relationship(
        "User",
        foreign_keys=[reviewed_by],  # 🔑 explicit FK for reviewer
        viewonly=True,  
        back_populates="reviewed_kyc_documents",
                       # optional if you don't modify via this relationship
    )
    
    def __repr__(self):
        return f"<KYCDocument {self.user_id} - {self.status}>"