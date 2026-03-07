"""
Gazette upload and extraction endpoints.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

from app.core.config import settings
from app.core.database import get_db
from app.core.permissions import Permission, require_permission
from app.models.gazette import Gazette, GazetteStatus
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
