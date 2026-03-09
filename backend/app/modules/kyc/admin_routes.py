"""Admin KYC review endpoints."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from app.core.database import get_db
from app.core.permissions import Permission, require_permission
from app.models.audit_log import AuditEventType, AuditLog
from app.modules.auth.models import User
from app.modules.kyc.models import KYCDocument, KYCStatus
from app.modules.kyc.schemas import (
    KYCAdminComparisonField,
    KYCAdminDetailResponse,
    KYCAdminPendingItem,
    KYCRejectRequest,
)
from app.services.email import send_email
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

router = APIRouter(prefix="/admin/kyc", tags=["admin-kyc"])
logger = logging.getLogger(__name__)


def _stringify(value: object | None) -> str | None:
    if value is None:
        return None
    return str(value).strip()


def _normalize(value: object | None) -> str:
    return (_stringify(value) or "").casefold()


def _merged_extracted_data(kyc: KYCDocument) -> dict[str, object]:
    extracted_data = kyc.extracted_data or {}
    merged: dict[str, object] = {}

    front = extracted_data.get("front")
    if isinstance(front, dict):
        merged.update(front)

    back = extracted_data.get("back")
    if isinstance(back, dict):
        merged.update(back)

    for key, value in extracted_data.items():
        if key not in {"front", "back"}:
            merged[key] = value

    return merged


def _user_provided_data(kyc: KYCDocument) -> dict[str, str | None]:
    payload = kyc.user_provided_data or {}
    return {
        "nic_number": _stringify(payload.get("nic_number")) or _stringify(kyc.nic_number),
        "full_name": _stringify(payload.get("full_name")) or _stringify(kyc.full_name),
        "date_of_birth": _stringify(payload.get("date_of_birth")) or _stringify(kyc.date_of_birth),
        "address": _stringify(payload.get("address")) or _stringify(kyc.address),
        "gender": _stringify(payload.get("gender")) or _stringify(kyc.gender),
    }


def _comparison_rows(kyc: KYCDocument) -> list[KYCAdminComparisonField]:
    extracted = _merged_extracted_data(kyc)
    user_data = _user_provided_data(kyc)
    fields = [
        ("nic_number", "NIC Number"),
        ("full_name", "Full Name"),
        ("date_of_birth", "Date of Birth"),
        ("address", "Address"),
        ("gender", "Gender"),
    ]

    rows: list[KYCAdminComparisonField] = []
    for field_name, label in fields:
        extracted_value = _stringify(extracted.get(field_name))
        user_value = user_data.get(field_name)
        matches = (
            not extracted_value
            or not user_value
            or _normalize(extracted_value) == _normalize(user_value)
        )
        rows.append(
            KYCAdminComparisonField(
                label=label,
                extracted_value=extracted_value,
                user_value=user_value,
                matches=matches,
            )
        )
    return rows


def _discrepancies(kyc: KYCDocument) -> dict[str, bool]:
    return {row.label.lower().replace(" ", "_"): not row.matches for row in _comparison_rows(kyc)}


def _extraction_method(kyc: KYCDocument) -> str:
    extracted = kyc.extracted_data or {}
    method = extracted.get("extraction_method")
    if isinstance(method, str) and method.strip():
        return method
    if kyc.status == KYCStatus.PENDING_MANUAL_REVIEW:
        return "manual_review_required"
    return "unknown"


def _auto_extracted(kyc: KYCDocument) -> bool:
    return bool((kyc.extracted_data or {}).get("front") or (kyc.extracted_data or {}).get("back"))


def _needs_manual_extraction(kyc: KYCDocument) -> bool:
    return kyc.status == KYCStatus.PENDING_MANUAL_REVIEW


def _serialize_pending_item(kyc: KYCDocument) -> KYCAdminPendingItem:
    return KYCAdminPendingItem(
        id=kyc.id,
        user_id=kyc.user_id,
        user_email=kyc.user.email,
        user_name=kyc.user.name or kyc.user.email,
        status=kyc.status.value,
        created_at=kyc.created_at,
        extraction_method=_extraction_method(kyc),
        auto_extracted=_auto_extracted(kyc),
        needs_manual_extraction=_needs_manual_extraction(kyc),
    )


def _serialize_detail(kyc: KYCDocument) -> KYCAdminDetailResponse:
    rows = _comparison_rows(kyc)
    return KYCAdminDetailResponse(
        id=kyc.id,
        user_id=kyc.user_id,
        user_email=kyc.user.email,
        user_name=kyc.user.name or kyc.user.email,
        status=kyc.status.value,
        created_at=kyc.created_at,
        reviewed_at=kyc.reviewed_at,
        reviewed_by=kyc.reviewed_by,
        rejection_reason=kyc.rejection_reason,
        nic_front_url=kyc.nic_front_url,
        nic_back_url=kyc.nic_back_url,
        selfie_url=kyc.selfie_url,
        extracted_data=kyc.extracted_data or {},
        user_provided_data=_user_provided_data(kyc),
        discrepancies={row.label.lower().replace(" ", "_"): not row.matches for row in rows},
        comparison_rows=rows,
        extraction_method=_extraction_method(kyc),
        auto_extracted=_auto_extracted(kyc),
        needs_manual_extraction=_needs_manual_extraction(kyc),
    )


async def _send_kyc_review_email(
    *,
    user_email: str,
    approved: bool,
    admin_email: str,
    reason: str | None = None,
) -> None:
    if approved:
        subject = "KYC Approved - ClearDrive.lk"
        html_content = (
            "<h2>KYC Approved</h2>"
            "<p>Your KYC documents have been approved.</p>"
            f"<p>Reviewed by: <strong>{admin_email}</strong></p>"
        )
        text_content = (
            "KYC Approved\n\n"
            "Your KYC documents have been approved.\n"
            f"Reviewed by: {admin_email}"
        )
    else:
        subject = "KYC Rejected - ClearDrive.lk"
        html_content = (
            "<h2>KYC Rejected</h2>"
            "<p>Your KYC documents have been rejected.</p>"
            f"<p>Reviewed by: <strong>{admin_email}</strong></p>"
            f"<p>Reason: {reason or 'No reason provided'}</p>"
        )
        text_content = (
            "KYC Rejected\n\n"
            "Your KYC documents have been rejected.\n"
            f"Reviewed by: {admin_email}\n"
            f"Reason: {reason or 'No reason provided'}"
        )

    sent = await send_email(user_email, subject, html_content, text_content)
    if not sent:
        logger.warning("Failed to send KYC review email to %s", user_email)


def _get_kyc_or_404(db: Session, kyc_id: str) -> KYCDocument:
    kyc = db.query(KYCDocument).filter(KYCDocument.id == kyc_id).first()
    if not kyc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KYC document not found")
    return kyc


@router.get("/pending", response_model=list[KYCAdminPendingItem])
async def get_pending_kyc_documents(
    status_filter: str | None = Query(
        default=None, alias="status", description="PENDING, PENDING_MANUAL_REVIEW, or ALL"
    ),
    current_user: User = Depends(require_permission(Permission.REVIEW_KYC)),
    db: Session = Depends(get_db),
):
    """Return KYC submissions waiting for admin review."""
    _ = current_user
    query = db.query(KYCDocument).join(User, User.id == KYCDocument.user_id)

    if status_filter == "PENDING":
        query = query.filter(KYCDocument.status == KYCStatus.PENDING)
    elif status_filter == "PENDING_MANUAL_REVIEW":
        query = query.filter(KYCDocument.status == KYCStatus.PENDING_MANUAL_REVIEW)
    elif status_filter in {None, "", "ALL"}:
        query = query.filter(
            or_(
                KYCDocument.status == KYCStatus.PENDING,
                KYCDocument.status == KYCStatus.PENDING_MANUAL_REVIEW,
            )
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status filter. Use PENDING, PENDING_MANUAL_REVIEW, or ALL.",
        )

    documents = query.order_by(KYCDocument.created_at.asc()).all()
    return [_serialize_pending_item(document) for document in documents]


@router.get("/{kyc_id}", response_model=KYCAdminDetailResponse)
async def get_kyc_review_detail(
    kyc_id: str,
    current_user: User = Depends(require_permission(Permission.REVIEW_KYC)),
    db: Session = Depends(get_db),
):
    """Return a detailed KYC review payload for admins."""
    _ = current_user
    return _serialize_detail(_get_kyc_or_404(db, kyc_id))


@router.post("/{kyc_id}/approve")
async def approve_kyc(
    kyc_id: str,
    current_user: User = Depends(require_permission(Permission.APPROVE_KYC)),
    db: Session = Depends(get_db),
):
    """Approve a KYC document."""
    kyc = _get_kyc_or_404(db, kyc_id)
    if kyc.status not in {KYCStatus.PENDING, KYCStatus.PENDING_MANUAL_REVIEW}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve KYC with status {kyc.status.value}",
        )

    now = datetime.now(UTC)
    kyc.status = KYCStatus.APPROVED
    kyc.reviewed_by = current_user.id
    kyc.reviewed_at = now
    kyc.rejection_reason = None

    db.add(
        AuditLog(
            event_type=AuditEventType.KYC_APPROVED,
            user_id=kyc.user_id,
            admin_id=current_user.id,
            details={"kyc_id": str(kyc.id), "approved_by": current_user.email},
        )
    )
    db.commit()
    db.refresh(kyc)

    try:
        await _send_kyc_review_email(
            user_email=kyc.user.email,
            approved=True,
            admin_email=current_user.email,
        )
    except Exception:
        logger.exception("Failed to send KYC approval email for kyc_id=%s", kyc.id)

    return {"message": "KYC approved successfully", "kyc_id": str(kyc.id)}


@router.post("/{kyc_id}/reject")
async def reject_kyc(
    kyc_id: str,
    payload: KYCRejectRequest,
    current_user: User = Depends(require_permission(Permission.REJECT_KYC)),
    db: Session = Depends(get_db),
):
    """Reject a KYC document with a mandatory reason."""
    reason = payload.reason.strip()
    if len(reason) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rejection reason must be at least 10 characters",
        )

    kyc = _get_kyc_or_404(db, kyc_id)
    if kyc.status not in {KYCStatus.PENDING, KYCStatus.PENDING_MANUAL_REVIEW}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject KYC with status {kyc.status.value}",
        )

    now = datetime.now(UTC)
    kyc.status = KYCStatus.REJECTED
    kyc.reviewed_by = current_user.id
    kyc.reviewed_at = now
    kyc.rejection_reason = reason

    db.add(
        AuditLog(
            event_type=AuditEventType.KYC_REJECTED,
            user_id=kyc.user_id,
            admin_id=current_user.id,
            details={"kyc_id": str(kyc.id), "rejected_by": current_user.email, "reason": reason},
        )
    )
    db.commit()
    db.refresh(kyc)

    try:
        await _send_kyc_review_email(
            user_email=kyc.user.email,
            approved=False,
            admin_email=current_user.email,
            reason=reason,
        )
    except Exception:
        logger.exception("Failed to send KYC rejection email for kyc_id=%s", kyc.id)

    return {"message": "KYC rejected successfully", "kyc_id": str(kyc.id), "reason": reason}
