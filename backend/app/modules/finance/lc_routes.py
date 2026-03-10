"""
Letter of Credit endpoints.
Author: Parindra Gallage
Story: CD-33.1, CD-33.2
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_admin
from app.modules.finance.models import LetterOfCredit, LCStatus
from app.modules.finance.schemas import (
    LCCreateRequest,
    LCApproveRequest,
    LCRejectRequest,
    LCResponse,
)
from app.modules.orders.models import Order
from app.modules.auth.models import User

router = APIRouter(prefix="/lc", tags=["letter-of-credit"])


@router.post("/request", response_model=LCResponse)
async def request_letter_of_credit(
    request: LCCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Request Letter of Credit for order.

    **Story**: CD-33.1

    **Process**:
    1. Customer provides bank details
    2. Specifies LC amount
    3. Submits request
    4. Admin reviews and approves/rejects

    **Access**: Customer (own orders)
    """

    # Verify order exists and belongs to user
    order = (
        db.query(Order)
        .filter(Order.id == request.order_id, Order.user_id == current_user.id)
        .first()
    )

    if not order:
        raise HTTPException(404, "Order not found")

    # Check if LC already exists for order
    existing_lc = (
        db.query(LetterOfCredit).filter(LetterOfCredit.order_id == request.order_id).first()
    )

    if existing_lc:
        raise HTTPException(400, "LC already requested for this order")

    # Create LC request
    lc = LetterOfCredit(
        order_id=request.order_id,
        user_id=current_user.id,
        bank_name=request.bank_name,
        bank_branch=request.bank_branch,
        account_number=request.account_number,
        amount=request.amount,
        status=LCStatus.PENDING,
    )

    db.add(lc)
    db.commit()
    db.refresh(lc)

    print(f"✅ LC requested: {lc.id} for order {order.id}")

    return lc


@router.post("/{lc_id}/approve", response_model=LCResponse)
async def approve_letter_of_credit(
    lc_id: str,
    request: LCApproveRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Approve Letter of Credit.

    **Story**: CD-33.2

    **Access**: Admin only
    """

    lc = db.query(LetterOfCredit).filter(LetterOfCredit.id == lc_id).first()

    if not lc:
        raise HTTPException(404, "LC not found")

    if lc.status != LCStatus.PENDING:
        raise HTTPException(400, f"LC already {lc.status.value}")

    # Update LC
    lc.status = LCStatus.APPROVED
    lc.lc_number = request.lc_number
    lc.beneficiary_name = request.beneficiary_name
    lc.beneficiary_bank = request.beneficiary_bank
    lc.beneficiary_account = request.beneficiary_account
    lc.issue_date = request.issue_date
    lc.expiry_date = request.expiry_date
    lc.admin_notes = request.admin_notes
    lc.reviewed_by = current_admin.id
    lc.reviewed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(lc)

    print(f"✅ LC approved: {lc.lc_number}")

    # TODO: Send email to customer

    return lc


@router.post("/{lc_id}/reject", response_model=LCResponse)
async def reject_letter_of_credit(
    lc_id: str,
    request: LCRejectRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Reject Letter of Credit.

    **Story**: CD-33.2

    **Access**: Admin only
    """

    lc = db.query(LetterOfCredit).filter(LetterOfCredit.id == lc_id).first()

    if not lc:
        raise HTTPException(404, "LC not found")

    if lc.status != LCStatus.PENDING:
        raise HTTPException(400, f"LC already {lc.status.value}")

    # Reject LC
    lc.status = LCStatus.REJECTED
    lc.rejection_reason = request.rejection_reason
    lc.reviewed_by = current_admin.id
    lc.reviewed_at = datetime.utcnow()

    db.commit()
    db.refresh(lc)

    print(f"❌ LC rejected: {lc.id}")

    # TODO: Send email to customer

    return lc


@router.get("/pending", response_model=List[LCResponse])
async def get_pending_lc_requests(
    current_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)
):
    """
    Get all pending LC requests (admin only).

    **Story**: CD-33.7
    """

    lcs = db.query(LetterOfCredit).filter(LetterOfCredit.status == LCStatus.PENDING).all()

    return lcs


@router.get("/my-requests", response_model=List[LCResponse])
async def get_my_lc_requests(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get user's LC requests."""

    lcs = db.query(LetterOfCredit).filter(LetterOfCredit.user_id == current_user.id).all()

    return lcs
