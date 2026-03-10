"""
Financial services models - LC, Finance, Insurance.
Author: Tharin
Story: CD-33
"""

from sqlalchemy import Column, String, DECIMAL, DateTime, ForeignKey, Text, Boolean, Enum as SQLEnum, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


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

class LetterOfCredit(Base):
    """
    Letter of Credit request and approval.
    
    Story: CD-33.1, CD-33.2
    
    LC is used for international payments in vehicle imports.
    Customer requests LC, admin reviews and approves.
    """
    
    __tablename__ = "letters_of_credit"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("orders.id"),
        nullable=False,
        unique=True  # One LC per order
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # LC Details
    lc_number = Column(String(50), unique=True, nullable=True)  # Generated after approval
    bank_name = Column(String(255), nullable=False)
    bank_branch = Column(String(255))
    account_number = Column(String(50), nullable=False)
    
    # Amount
    amount = Column(DECIMAL(12, 2), nullable=False)
    currency = Column(String(3), default='LKR')
    
    # Beneficiary (Exporter)
    beneficiary_name = Column(String(255))
    beneficiary_bank = Column(String(255))
    beneficiary_account = Column(String(100))
    
    # Status
    status = Column(SQLEnum(LCStatus), default=LCStatus.PENDING)
    
    # Review
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)
    
    # Validity
    issue_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    
    # Documents
    documents_required = Column(Text)  # JSON list
    documents_submitted = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order = relationship("Order", back_populates="letter_of_credit")
    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    
    def __repr__(self):
        return f"<LetterOfCredit {self.lc_number or self.id} - {self.status.value}>"


# ===================================================================
# VEHICLE FINANCE MODEL (CD-33.3)
# ===================================================================

class VehicleFinance(Base):
    """
    Vehicle finance/loan application.
    
    Story: CD-33.3, CD-33.4
    
    Customer applies for loan to finance vehicle purchase.
    Admin reviews and approves with loan terms.
    """
    
    __tablename__ = "vehicle_finance"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("orders.id"),
        nullable=False,
        unique=True
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Loan Details
    loan_number = Column(String(50), unique=True, nullable=True)
    vehicle_price = Column(DECIMAL(12, 2), nullable=False)
    down_payment = Column(DECIMAL(12, 2), nullable=False)
    loan_amount = Column(DECIMAL(12, 2), nullable=False)
    
    # Customer Info
    monthly_income = Column(DECIMAL(12, 2), nullable=False)
    employment_type = Column(String(50))  # Permanent, Contract, Self-employed
    employer_name = Column(String(255))
    years_employed = Column(DECIMAL(4, 1))
    
    # Loan Terms (Set by admin on approval)
    interest_rate = Column(DECIMAL(5, 2), nullable=True)  # e.g., 12.50%
    loan_period_months = Column(Integer, nullable=True)  # e.g., 60 months
    monthly_payment = Column(DECIMAL(12, 2), nullable=True)
    
    # Status
    status = Column(SQLEnum(FinanceStatus), default=FinanceStatus.PENDING)
    
    # Review
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)
    
    # Disbursement
    disbursed_at = Column(DateTime, nullable=True)
    disbursement_reference = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order = relationship("Order", back_populates="vehicle_finance")
    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    
    def __repr__(self):
        return f"<VehicleFinance {self.loan_number or self.id} - {self.status.value}>"


# ===================================================================
# VEHICLE INSURANCE MODEL (CD-33.5)
# ===================================================================

class VehicleInsurance(Base):
    """
    Vehicle insurance quote and approval.
    
    Story: CD-33.5, CD-33.6
    
    Customer requests insurance quote for imported vehicle.
    Admin reviews and provides quote with premium amount.
    """
    
    __tablename__ = "vehicle_insurance"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("orders.id"),
        nullable=False,
        unique=True
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Policy Details
    policy_number = Column(String(50), unique=True, nullable=True)
    insurance_type = Column(String(50))  # Comprehensive, Third Party, etc.
    
    # Vehicle Info (from order)
    vehicle_value = Column(DECIMAL(12, 2), nullable=False)
    
    # Coverage
    coverage_amount = Column(DECIMAL(12, 2), nullable=True)
    deductible = Column(DECIMAL(12, 2), nullable=True)
    
    # Premium
    annual_premium = Column(DECIMAL(12, 2), nullable=True)
    payment_frequency = Column(String(20), nullable=True)  # Annual, Semi-annual, Quarterly
    
    # Driver Info
    driver_age = Column(Integer, nullable=False)
    driver_experience_years = Column(Integer, nullable=False)
    license_number = Column(String(50))
    previous_claims = Column(Integer, default=0)
    
    # Status
    status = Column(SQLEnum(InsuranceStatus), default=InsuranceStatus.PENDING)
    
    # Review
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)
    
    # Policy Period
    policy_start_date = Column(DateTime, nullable=True)
    policy_end_date = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order = relationship("Order", back_populates="vehicle_insurance")
    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    
    def __repr__(self):
        return f"<VehicleInsurance {self.policy_number or self.id} - {self.status.value}>"
