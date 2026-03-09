"""
Gazette upload and extraction endpoints.
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.core.config import settings
from app.core.database import get_db
from app.core.permissions import Permission, require_permission
from app.models.audit_log import AuditEventType, AuditLog
from app.models.gazette import (
    ApplyOn,
    Gazette,
    GazetteStatus,
    TaxFuelType,
    TaxRule,
    TaxVehicleType,
)
from app.modules.auth.models import User
from app.services.document_ai import document_ai_service
from app.services.gemini import gemini_service
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter(prefix="/gazette", tags=["Gazette"])
logger = logging.getLogger(__name__)


class GazetteUploadResponse(BaseModel):
    gazette_id: str
    gazette_no: str
    effective_date: str | None
    rules_count: int
    confidence: float
    status: str
    preview: dict[str, Any]
    message: str | None = None


class GazetteDecisionRequest(BaseModel):
    reason: str | None = None


def _parse_effective_date(raw_value: Any) -> date | None:
    if raw_value is None:
        return None
    value = str(raw_value).strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _coerce_decimal(value: Any, default: str = "0") -> Decimal:
    if value is None or value == "":
        return Decimal(default)
    return Decimal(str(value))


def _parse_gazette_id(gazette_id: str) -> UUID:
    try:
        return UUID(gazette_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid gazette_id") from exc


def _parse_tax_rules(gazette: Gazette, approved_by: User) -> list[TaxRule]:
    payload = gazette.raw_extracted or {}
    raw_rules = payload.get("rules")
    if not isinstance(raw_rules, list) or not raw_rules:
        raise HTTPException(status_code=400, detail="Gazette has no extracted tax rules to approve")

    effective_date = gazette.effective_date or _parse_effective_date(payload.get("effective_date"))
    if effective_date is None:
        raise HTTPException(
            status_code=400, detail="Gazette effective date is required for approval"
        )

    rules: list[TaxRule] = []
    for rule in raw_rules:
        try:
            vehicle_type = TaxVehicleType(str(rule["vehicle_type"]).upper()).value
            fuel_type = TaxFuelType(str(rule["fuel_type"]).upper()).value
            apply_on = ApplyOn(str(rule.get("apply_on", ApplyOn.CIF.value)).upper()).value
        except Exception as exc:
            raise HTTPException(
                status_code=400, detail="Gazette contains invalid tax rule values"
            ) from exc

        rules.append(
            TaxRule(
                gazette_id=gazette.id,
                vehicle_type=vehicle_type,
                fuel_type=fuel_type,
                engine_min=int(rule.get("engine_min", 0) or 0),
                engine_max=int(rule.get("engine_max", 999999) or 999999),
                customs_percent=_coerce_decimal(rule.get("customs_percent")),
                excise_percent=_coerce_decimal(rule.get("excise_percent")),
                vat_percent=_coerce_decimal(rule.get("vat_percent"), "15"),
                pal_percent=_coerce_decimal(rule.get("pal_percent"), "0"),
                cess_percent=_coerce_decimal(rule.get("cess_percent"), "0"),
                apply_on=apply_on,
                effective_date=effective_date,
                approved_by_admin=approved_by.id,
                is_active=True,
                notes=str(rule.get("notes") or "") or None,
            )
        )
    return rules


@router.post("/upload", response_model=GazetteUploadResponse)
async def upload_gazette(
    file: UploadFile = File(...),
    gazette_no: str = Form(...),
    current_user: User = Depends(require_permission(Permission.MANAGE_USERS)),
    db: Session = Depends(get_db),
) -> GazetteUploadResponse:
    """Upload a gazette PDF, extract rules, and save for admin review."""
    filename = (file.filename or "").lower()
    if not filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )

    content = await file.read()
    max_size_bytes = settings.MAX_GAZETTE_SIZE_MB * 1024 * 1024
    if len(content) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.MAX_GAZETTE_SIZE_MB}MB",
        )

    existing = db.query(Gazette).filter(Gazette.gazette_no == gazette_no).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Gazette {gazette_no} already exists (status: {existing.status})",
        )

    try:
        extraction = await document_ai_service.parse_gazette_pdf(content)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse gazette PDF: {exc}",
        ) from exc

    try:
        structured = await gemini_service.structure_gazette(
            raw_text=extraction.get("text", ""),
            tables=extraction.get("tables", []),
            gazette_no=gazette_no,
        )
        effective = _parse_effective_date(structured.get("effective_date"))

        gazette = Gazette(
            gazette_no=gazette_no,
            effective_date=effective,
            raw_extracted=structured,
            status=GazetteStatus.PENDING.value,
            uploaded_by=current_user.id,
        )
        db.add(gazette)
        db.flush()
        db.add(
            AuditLog(
                event_type=AuditEventType.GAZETTE_UPLOADED,
                user_id=current_user.id,
                admin_id=current_user.id,
                details={
                    "gazette_id": str(gazette.id),
                    "gazette_no": gazette.gazette_no,
                    "rules_count": len(structured.get("rules", [])),
                    "uploaded_by": current_user.email,
                },
            )
        )
        db.commit()
        db.refresh(gazette)

        return GazetteUploadResponse(
            gazette_id=str(gazette.id),
            gazette_no=gazette.gazette_no,
            effective_date=structured.get("effective_date"),
            rules_count=len(structured.get("rules", [])),
            confidence=float(extraction.get("confidence", 0.0)),
            status=GazetteStatus.PENDING.value,
            preview=structured,
        )
    except Exception as exc:
        logger.warning("Gemini structuring failed for %s: %s", gazette_no, exc)

        fallback_payload = {
            "error": str(exc),
            "text": extraction.get("text", "")[:1000],
            "tables": extraction.get("tables", []),
            "gazette_no": gazette_no,
        }

        gazette = Gazette(
            gazette_no=gazette_no,
            effective_date=None,
            raw_extracted=fallback_payload,
            status=GazetteStatus.PENDING.value,
            uploaded_by=current_user.id,
        )
        db.add(gazette)
        db.flush()
        db.add(
            AuditLog(
                event_type=AuditEventType.GAZETTE_UPLOADED,
                user_id=current_user.id,
                admin_id=current_user.id,
                details={
                    "gazette_id": str(gazette.id),
                    "gazette_no": gazette.gazette_no,
                    "rules_count": 0,
                    "uploaded_by": current_user.email,
                    "message": "Automatic extraction failed. Manual review required.",
                },
            )
        )
        db.commit()
        db.refresh(gazette)

        return GazetteUploadResponse(
            gazette_id=str(gazette.id),
            gazette_no=gazette.gazette_no,
            effective_date=None,
            rules_count=0,
            confidence=float(extraction.get("confidence", 0.0)),
            status="NEEDS_MANUAL_REVIEW",
            preview=fallback_payload,
            message="Automatic extraction failed. Manual review required.",
        )


@router.post("/{gazette_id}/approve")
async def approve_gazette(
    gazette_id: str,
    current_user: User = Depends(require_permission(Permission.APPROVE_TAX_RULES)),
    db: Session = Depends(get_db),
):
    parsed_gazette_id = _parse_gazette_id(gazette_id)
    gazette = db.query(Gazette).filter(Gazette.id == parsed_gazette_id).first()
    if gazette is None:
        raise HTTPException(status_code=404, detail="Gazette not found")
    if gazette.status == GazetteStatus.APPROVED.value:
        raise HTTPException(status_code=400, detail="Gazette is already approved")

    rules = _parse_tax_rules(gazette, current_user)
    db.query(TaxRule).filter(TaxRule.is_active.is_(True)).update({"is_active": False})
    gazette.status = GazetteStatus.APPROVED.value
    gazette.approved_by = current_user.id
    gazette.rejection_reason = None
    for rule in rules:
        db.add(rule)
    db.add(
        AuditLog(
            event_type=AuditEventType.GAZETTE_APPROVED,
            user_id=gazette.uploaded_by,
            admin_id=current_user.id,
            details={
                "gazette_id": str(gazette.id),
                "gazette_no": gazette.gazette_no,
                "approved_by": current_user.email,
                "rules_count": len(rules),
            },
        )
    )
    db.add(
        AuditLog(
            event_type=AuditEventType.TAX_RULES_ACTIVATED,
            user_id=gazette.uploaded_by,
            admin_id=current_user.id,
            details={
                "gazette_id": str(gazette.id),
                "gazette_no": gazette.gazette_no,
                "rules_activated": len(rules),
                "effective_date": (
                    gazette.effective_date.isoformat() if gazette.effective_date else None
                ),
            },
        )
    )
    db.commit()
    return {"message": "Gazette approved successfully", "gazette_id": str(gazette.id)}


@router.post("/{gazette_id}/reject")
async def reject_gazette(
    gazette_id: str,
    payload: GazetteDecisionRequest,
    current_user: User = Depends(require_permission(Permission.APPROVE_TAX_RULES)),
    db: Session = Depends(get_db),
):
    parsed_gazette_id = _parse_gazette_id(gazette_id)
    gazette = db.query(Gazette).filter(Gazette.id == parsed_gazette_id).first()
    if gazette is None:
        raise HTTPException(status_code=404, detail="Gazette not found")

    reason = (payload.reason or "").strip()
    if len(reason) < 10:
        raise HTTPException(status_code=400, detail="Reason must be at least 10 characters")

    gazette.status = GazetteStatus.REJECTED.value
    gazette.approved_by = current_user.id
    gazette.rejection_reason = reason
    db.add(
        AuditLog(
            event_type=AuditEventType.GAZETTE_REJECTED,
            user_id=gazette.uploaded_by,
            admin_id=current_user.id,
            details={
                "gazette_id": str(gazette.id),
                "gazette_no": gazette.gazette_no,
                "rejected_by": current_user.email,
                "reason": reason,
            },
        )
    )
    db.commit()
    return {"message": "Gazette rejected successfully", "gazette_id": str(gazette.id)}
