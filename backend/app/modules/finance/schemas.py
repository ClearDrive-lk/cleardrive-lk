"""
Financial services schemas.
Author: Parindra Gallage
Story: CD-33
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal


# ===================================================================
# LETTER OF CREDIT SCHEMAS (CD-33.1, CD-33.2)
# ===================================================================

class LCCreateRequest(BaseModel):
    """Request to create Letter of Credit."""
    
    order_id: UUID
    bank_name: str = Field(..., min_length=3, max_length=255)
    bank_branch: Optional[str] = Field(None, max_length=255)
    account_number: str = Field(..., min_length=5, max_length=50)
    amount: Decimal = Field(..., gt=0)


class LCApproveRequest(BaseModel):
    """Admin approval of LC."""
    
    lc_number: str = Field(..., min_length=5, max_length=50)
    beneficiary_name: str
    beneficiary_bank: str
    beneficiary_account: str
    issue_date: datetime
    expiry_date: datetime
    admin_notes: Optional[str] = None


class LCRejectRequest(BaseModel):
    """Admin rejection of LC."""
    
    rejection_reason: str = Field(..., min_length=10, max_length=500)


class LCResponse(BaseModel):
    """LC response."""
    
    id: UUID
    order_id: UUID
    lc_number: Optional[str]
    bank_name: str
    amount: Decimal
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===================================================================
# VEHICLE FINANCE SCHEMAS (CD-33.3, CD-33.4)
# ===================================================================

class FinanceApplicationRequest(BaseModel):
    """Finance loan application."""
    
    order_id: UUID
    vehicle_price: Decimal = Field(..., gt=0)
    down_payment: Decimal = Field(..., gt=0)
    monthly_income: Decimal = Field(..., gt=0)
    employment_type: str = Field(..., max_length=50)
    employer_name: str = Field(..., max_length=255)
    years_employed: Decimal = Field(..., ge=0)
    
    @validator('down_payment')
    def validate_down_payment(cls, v, values):
        if 'vehicle_price' in values and v > values['vehicle_price']:
            raise ValueError('Down payment cannot exceed vehicle price')
        return v


class FinanceApproveRequest(BaseModel):
    """Admin approval of finance."""
    
    loan_number: str = Field(..., min_length=5, max_length=50)
    interest_rate: Decimal = Field(..., gt=0, le=100)  # Percentage
    loan_period_months: int = Field(..., gt=0, le=120)  # Max 10 years
    admin_notes: Optional[str] = None


class FinanceRejectRequest(BaseModel):
    """Admin rejection of finance."""
    
    rejection_reason: str = Field(..., min_length=10, max_length=500)


class FinanceResponse(BaseModel):
    """Finance response."""
    
    id: UUID
    order_id: UUID
    loan_number: Optional[str]
    loan_amount: Decimal
    interest_rate: Optional[Decimal]
    loan_period_months: Optional[int]
    monthly_payment: Optional[Decimal]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===================================================================
# VEHICLE INSURANCE SCHEMAS (CD-33.5, CD-33.6)
# ===================================================================

class InsuranceQuoteRequest(BaseModel):
    """Insurance quote request."""
    
    order_id: UUID
    insurance_type: str = Field(..., max_length=50)
    vehicle_value: Decimal = Field(..., gt=0)
    driver_age: int = Field(..., ge=18, le=100)
    driver_experience_years: int = Field(..., ge=0, le=80)
    license_number: str = Field(..., max_length=50)
    previous_claims: int = Field(default=0, ge=0)


class InsuranceApproveRequest(BaseModel):
    """Admin approval of insurance with quote."""
    
    policy_number: str = Field(..., min_length=5, max_length=50)
    coverage_amount: Decimal = Field(..., gt=0)
    annual_premium: Decimal = Field(..., gt=0)
    deductible: Decimal = Field(..., ge=0)
    payment_frequency: str = Field(..., max_length=20)
    policy_start_date: datetime
    policy_end_date: datetime
    admin_notes: Optional[str] = None


class InsuranceRejectRequest(BaseModel):
    """Admin rejection of insurance."""
    
    rejection_reason: str = Field(..., min_length=10, max_length=500)


class InsuranceResponse(BaseModel):
    """Insurance response."""
    
    id: UUID
    order_id: UUID
    policy_number: Optional[str]
    insurance_type: str
    vehicle_value: Decimal
    annual_premium: Optional[Decimal]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True
