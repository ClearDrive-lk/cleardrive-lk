"""
Vehicle finance endpoints.
Author: Parindra Gallage
Story: CD-33.3, CD-33.4
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_finance_partner, get_current_user
from app.modules.auth.models import User
from app.modules.finance.models import FinanceStatus, VehicleFinance
from app.modules.finance.schemas import (
    FinanceApplicationRequest,
    FinanceApproveRequest,
    FinanceRejectRequest,
    FinanceResponse,
)
from app.modules.orders.models import Order
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(prefix="/finance", tags=["vehicle-finance"])


@router.post("/apply", response_model=FinanceResponse)
async def apply_for_finance(
    request: FinanceApplicationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Apply for vehicle finance/loan.

    **Story**: CD-33.3

    **Process**:
    1. Customer provides financial info
    2. Specifies down payment
    3. Submits application
    4. Admin reviews and approves with loan terms
    """

    # Verify order
    order = (
        db.query(Order)
        .filter(Order.id == request.order_id, Order.user_id == current_user.id)
        .first()
    )

    if not order:
        raise HTTPException(404, "Order not found")

    # Check existing application
    existing = db.query(VehicleFinance).filter(VehicleFinance.order_id == request.order_id).first()

    if existing:
        raise HTTPException(400, "Finance application already submitted")

    # Calculate loan amount
    loan_amount = request.vehicle_price - request.down_payment

    # Create application
    finance = VehicleFinance(
        order_id=request.order_id,
        user_id=current_user.id,
        vehicle_price=request.vehicle_price,
        down_payment=request.down_payment,
        loan_amount=loan_amount,
        monthly_income=request.monthly_income,
        employment_type=request.employment_type,
        employer_name=request.employer_name,
        years_employed=request.years_employed,
        status=FinanceStatus.PENDING,
    )

    db.add(finance)
    db.commit()
    db.refresh(finance)

    print(f"✅ Finance application: {finance.id} for LKR {loan_amount}")

    return finance


@router.post("/{finance_id}/approve", response_model=FinanceResponse)
async def approve_finance(
    finance_id: str,
    request: FinanceApproveRequest,
    current_finance_reviewer: User = Depends(get_current_finance_partner),
    db: Session = Depends(get_db),
):
    """
    Approve finance application with loan terms.

    **Story**: CD-33.4
    """

    finance = db.query(VehicleFinance).filter(VehicleFinance.id == finance_id).first()

    if not finance:
        raise HTTPException(404, "Finance application not found")

    if finance.status != FinanceStatus.PENDING:
        raise HTTPException(400, f"Application already {finance.status.value}")

    # Calculate monthly payment
    # Simple formula: P * r * (1 + r)^n / ((1 + r)^n - 1)
    # where P = loan amount, r = monthly interest rate, n = number of months

    monthly_rate = float(request.interest_rate) / 100 / 12
    n = request.loan_period_months

    if monthly_rate > 0:
        monthly_payment = (
            float(finance.loan_amount)
            * monthly_rate
            * (1 + monthly_rate) ** n
            / ((1 + monthly_rate) ** n - 1)
        )
    else:
        monthly_payment = float(finance.loan_amount) / n

    # Update finance
    finance.status = FinanceStatus.APPROVED
    finance.loan_number = request.loan_number
    finance.interest_rate = request.interest_rate
    finance.loan_period_months = request.loan_period_months
    finance.monthly_payment = Decimal(str(round(monthly_payment, 2)))
    finance.admin_notes = request.admin_notes
    finance.reviewed_by = current_finance_reviewer.id
    finance.reviewed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(finance)

    print(f"✅ Finance approved: {finance.loan_number}")
    print(f"   Loan Amount: LKR {finance.loan_amount}")
    print(f"   Interest Rate: {finance.interest_rate}%")
    print(f"   Period: {finance.loan_period_months} months")
    print(f"   Monthly Payment: LKR {finance.monthly_payment}")

    # TODO: Send email to customer

    return finance


@router.post("/{finance_id}/reject", response_model=FinanceResponse)
async def reject_finance(
    finance_id: str,
    request: FinanceRejectRequest,
    current_finance_reviewer: User = Depends(get_current_finance_partner),
    db: Session = Depends(get_db),
):
    """Reject finance application."""

    finance = db.query(VehicleFinance).filter(VehicleFinance.id == finance_id).first()

    if not finance:
        raise HTTPException(404, "Finance application not found")

    if finance.status != FinanceStatus.PENDING:
        raise HTTPException(400, f"Application already {finance.status.value}")

    finance.status = FinanceStatus.REJECTED
    finance.rejection_reason = request.rejection_reason
    finance.reviewed_by = current_finance_reviewer.id
    finance.reviewed_at = datetime.utcnow()

    db.commit()
    db.refresh(finance)

    print(f"❌ Finance rejected: {finance.id}")

    return finance


@router.get("/pending", response_model=List[FinanceResponse])
async def get_pending_finance_applications(
    current_finance_reviewer: User = Depends(get_current_finance_partner),
    db: Session = Depends(get_db),
):
    """Get pending finance applications (admin)."""

    _ = current_finance_reviewer
    applications = (
        db.query(VehicleFinance).filter(VehicleFinance.status == FinanceStatus.PENDING).all()
    )

    return applications
