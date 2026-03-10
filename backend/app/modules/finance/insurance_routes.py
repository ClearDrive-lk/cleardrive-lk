"""
Vehicle insurance endpoints.
Author: Parindra Gallage
Story: CD-33.5, CD-33.6
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_admin
from app.modules.finance.models import VehicleInsurance, InsuranceStatus
from app.modules.finance.schemas import (
    InsuranceQuoteRequest,
    InsuranceApproveRequest,
    InsuranceRejectRequest,
    InsuranceResponse,
)
from app.modules.orders.models import Order
from app.modules.auth.models import User

router = APIRouter(prefix="/insurance", tags=["vehicle-insurance"])


@router.post("/quote", response_model=InsuranceResponse)
async def request_insurance_quote(
    request: InsuranceQuoteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Request insurance quote.

    **Story**: CD-33.5
    """

    # Verify order
    order = (
        db.query(Order)
        .filter(Order.id == request.order_id, Order.user_id == current_user.id)
        .first()
    )

    if not order:
        raise HTTPException(404, "Order not found")

    # Check existing quote
    existing = (
        db.query(VehicleInsurance).filter(VehicleInsurance.order_id == request.order_id).first()
    )

    if existing:
        raise HTTPException(400, "Insurance quote already requested")

    # Create quote request
    insurance = VehicleInsurance(
        order_id=request.order_id,
        user_id=current_user.id,
        insurance_type=request.insurance_type,
        vehicle_value=request.vehicle_value,
        driver_age=request.driver_age,
        driver_experience_years=request.driver_experience_years,
        license_number=request.license_number,
        previous_claims=request.previous_claims,
        status=InsuranceStatus.PENDING,
    )

    db.add(insurance)
    db.commit()
    db.refresh(insurance)

    print(f"✅ Insurance quote requested: {insurance.id}")

    return insurance


@router.post("/{insurance_id}/approve", response_model=InsuranceResponse)
async def approve_insurance_quote(
    insurance_id: str,
    request: InsuranceApproveRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Approve insurance with quote.

    **Story**: CD-33.6
    """

    insurance = db.query(VehicleInsurance).filter(VehicleInsurance.id == insurance_id).first()

    if not insurance:
        raise HTTPException(404, "Insurance quote not found")

    if insurance.status != InsuranceStatus.PENDING:
        raise HTTPException(400, f"Quote already {insurance.status.value}")

    # Update insurance
    insurance.status = InsuranceStatus.QUOTED
    insurance.policy_number = request.policy_number
    insurance.coverage_amount = request.coverage_amount
    insurance.annual_premium = request.annual_premium
    insurance.deductible = request.deductible
    insurance.payment_frequency = request.payment_frequency
    insurance.policy_start_date = request.policy_start_date
    insurance.policy_end_date = request.policy_end_date
    insurance.admin_notes = request.admin_notes
    insurance.reviewed_by = current_admin.id
    insurance.reviewed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(insurance)

    print(f"✅ Insurance quoted: {insurance.policy_number}")
    print(f"   Annual Premium: LKR {insurance.annual_premium}")

    # TODO: Send email to customer

    return insurance


@router.post("/{insurance_id}/reject", response_model=InsuranceResponse)
async def reject_insurance_quote(
    insurance_id: str,
    request: InsuranceRejectRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Reject insurance quote."""

    insurance = db.query(VehicleInsurance).filter(VehicleInsurance.id == insurance_id).first()

    if not insurance:
        raise HTTPException(404, "Insurance quote not found")

    if insurance.status != InsuranceStatus.PENDING:
        raise HTTPException(400, f"Quote already {insurance.status.value}")

    insurance.status = InsuranceStatus.REJECTED
    insurance.rejection_reason = request.rejection_reason
    insurance.reviewed_by = current_admin.id
    insurance.reviewed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(insurance)

    print(f"❌ Insurance rejected: {insurance.id}")

    return insurance


@router.get("/pending", response_model=List[InsuranceResponse])
async def get_pending_insurance_quotes(
    current_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)
):
    """Get pending insurance quotes (admin)."""

    quotes = (
        db.query(VehicleInsurance).filter(VehicleInsurance.status == InsuranceStatus.PENDING).all()
    )

    return quotes
