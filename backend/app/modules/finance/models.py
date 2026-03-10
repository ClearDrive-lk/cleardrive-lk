"""
Financial services models - LC, Finance, Insurance.
Author: Parindra Gallage
Story: CD-33
"""

from __future__ import annotations

import enum
from datetime import datetime as dt
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID as PyUUID

from app.core.database import Base
from app.core.models import GUID, TimestampMixin, UUIDMixin
from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, Integer
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.modules.auth.models import User
    from app.modules.orders.models import Order


# ===================================================================
# ENUMS
# ===================================================================

class LCStatus(str, enum.Enum):
    """Letter of Credit status."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ISSUED = "ISSUED"
    EXPIRED = "EXPIRED"


class FinanceStatus(str, enum.Enum):
    """Finance loan status."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DISBURSED = "DISBURSED"
    COMPLETED = "COMPLETED"


class InsuranceStatus(str, enum.Enum):
    """Insurance status."""
    PENDING = "PENDING"
    QUOTED = "QUOTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"


# ===================================================================
# LETTER OF CREDIT MODEL (CD-33.1)
# ===================================================================

class LetterOfCredit(Base, UUIDMixin, TimestampMixin):
    """
    Letter of Credit request and approval.
    
    Story: CD-33.1, CD-33.2
    
    LC is used for international payments in vehicle imports.
    Customer requests LC, admin reviews and approves.
    """
    
    __tablename__ = "letters_of_credit"
    
    # Foreign Keys
    order_id: Mapped[PyUUID] = mapped_column(
        GUID(),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        unique=True  # One LC per order
    )
    user_id: Mapped[PyUUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # LC Details
    lc_number: Mapped[str | None] = mapped_column(String(50), unique=True)  # Generated after approval
    bank_name: Mapped[str] = mapped_column(String(255), nullable=False)
    bank_branch: Mapped[str | None] = mapped_column(String(255))
    account_number: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Amount
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default='LKR')
    
    # Beneficiary (Exporter)
    beneficiary_name: Mapped[str | None] = mapped_column(String(255))
    beneficiary_bank: Mapped[str | None] = mapped_column(String(255))
    beneficiary_account: Mapped[str | None] = mapped_column(String(100))
    
    # Status
    status: Mapped[LCStatus] = mapped_column(SQLEnum(LCStatus), default=LCStatus.PENDING)
    
    # Review
    reviewed_by: Mapped[PyUUID | None] = mapped_column(GUID(), ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at: Mapped[dt | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    admin_notes: Mapped[str | None] = mapped_column(Text)
    
    # Validity
    issue_date: Mapped[dt | None] = mapped_column(DateTime(timezone=True))
    expiry_date: Mapped[dt | None] = mapped_column(DateTime(timezone=True))
    
    # Documents
    documents_required: Mapped[str | None] = mapped_column(Text)  # JSON list
    documents_submitted: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    order: Mapped[Order] = relationship("Order", back_populates="letter_of_credit")
    user: Mapped[User] = relationship("User", foreign_keys=[user_id])
    reviewer: Mapped[User | None] = relationship("User", foreign_keys=[reviewed_by])
    
    def __repr__(self):
        return f"<LetterOfCredit {self.lc_number or self.id} - {self.status.value}>"


# ===================================================================
# VEHICLE FINANCE MODEL (CD-33.3)
# ===================================================================

class VehicleFinance(Base, UUIDMixin, TimestampMixin):
    """
    Vehicle finance/loan application.
    
    Story: CD-33.3, CD-33.4
    
    Customer applies for loan to finance vehicle purchase.
    Admin reviews and approves with loan terms.
    """
    
    __tablename__ = "vehicle_finance"
    
    # Foreign Keys
    order_id: Mapped[PyUUID] = mapped_column(
        GUID(),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    user_id: Mapped[PyUUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Loan Details
    loan_number: Mapped[str | None] = mapped_column(String(50), unique=True)
    vehicle_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    down_payment: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    loan_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    
    # Customer Info
    monthly_income: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    employment_type: Mapped[str | None] = mapped_column(String(50))  # Permanent, Contract, Self-employed
    employer_name: Mapped[str | None] = mapped_column(String(255))
    years_employed: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    
    # Loan Terms (Set by admin on approval)
    interest_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))  # e.g., 12.50%
    loan_period_months: Mapped[int | None] = mapped_column(Integer)  # e.g., 60 months
    monthly_payment: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    
    # Status
    status: Mapped[FinanceStatus] = mapped_column(SQLEnum(FinanceStatus), default=FinanceStatus.PENDING)
    
    # Review
    reviewed_by: Mapped[PyUUID | None] = mapped_column(GUID(), ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at: Mapped[dt | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    admin_notes: Mapped[str | None] = mapped_column(Text)
    
    # Disbursement
    disbursed_at: Mapped[dt | None] = mapped_column(DateTime(timezone=True))
    disbursement_reference: Mapped[str | None] = mapped_column(String(100))
    
    # Relationships
    order: Mapped[Order] = relationship("Order", back_populates="vehicle_finance")
    user: Mapped[User] = relationship("User", foreign_keys=[user_id])
    reviewer: Mapped[User | None] = relationship("User", foreign_keys=[reviewed_by])
    
    def __repr__(self):
        return f"<VehicleFinance {self.loan_number or self.id} - {self.status.value}>"


# ===================================================================
# VEHICLE INSURANCE MODEL (CD-33.5)
# ===================================================================

class VehicleInsurance(Base, UUIDMixin, TimestampMixin):
    """
    Vehicle insurance quote and approval.
    
    Story: CD-33.5, CD-33.6
    
    Customer requests insurance quote for imported vehicle.
    Admin reviews and provides quote with premium amount.
    """
    
    __tablename__ = "vehicle_insurance"
    
    # Foreign Keys
    order_id: Mapped[PyUUID] = mapped_column(
        GUID(),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    user_id: Mapped[PyUUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Policy Details
    policy_number: Mapped[str | None] = mapped_column(String(50), unique=True)
    insurance_type: Mapped[str | None] = mapped_column(String(50))  # Comprehensive, Third Party, etc.
    
    # Vehicle Info (from order)
    vehicle_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    
    # Coverage
    coverage_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    deductible: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    
    # Premium
    annual_premium: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    payment_frequency: Mapped[str | None] = mapped_column(String(20))  # Annual, Semi-annual, Quarterly
    
    # Driver Info
    driver_age: Mapped[int] = mapped_column(Integer, nullable=False)
    driver_experience_years: Mapped[int] = mapped_column(Integer, nullable=False)
    license_number: Mapped[str | None] = mapped_column(String(50))
    previous_claims: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status
    status: Mapped[InsuranceStatus] = mapped_column(SQLEnum(InsuranceStatus), default=InsuranceStatus.PENDING)
    
    # Review
    reviewed_by: Mapped[PyUUID | None] = mapped_column(GUID(), ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at: Mapped[dt | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    admin_notes: Mapped[str | None] = mapped_column(Text)
    
    # Policy Period
    policy_start_date: Mapped[dt | None] = mapped_column(DateTime(timezone=True))
    policy_end_date: Mapped[dt | None] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    order: Mapped[Order] = relationship("Order", back_populates="vehicle_insurance")
    user: Mapped[User] = relationship("User", foreign_keys=[user_id])
    reviewer: Mapped[User | None] = relationship("User", foreign_keys=[reviewed_by])
    
    def __repr__(self):
        return f"<VehicleInsurance {self.policy_number or self.id} - {self.status.value}>"
