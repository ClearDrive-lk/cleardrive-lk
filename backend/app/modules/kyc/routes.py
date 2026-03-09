# backend/app/modules/kyc/routes.py

"""
KYC document upload endpoint.
Story: CD-50 - KYC Document Upload
"""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC
from datetime import date as dt_date
from datetime import datetime
from typing import TypedDict, cast

try:
    import magic
except ImportError:
    magic = None  # type: ignore[assignment]
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.storage import storage
from app.modules.auth.models import User
from app.modules.kyc.models import KYCDocument, KYCStatus
from app.modules.kyc.schemas import (
    KYCStatusResponse,
    KYCUploadResponse,
    KYCUploadResultResponse,
)
from app.modules.security.models import FileIntegrity, VerificationStatus
from app.services.email import send_email
from app.services.vps_proxy import extract_nic_with_retry
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/kyc", tags=["kyc"])
logger = logging.getLogger(__name__)


class KYCFilePayload(TypedDict):
    content: bytes
    mime_type: str
    size: int


MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # CD-50.4 (10MB)
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _parse_optional_date(value: str | None) -> dt_date | None:
    if not value or not value.strip():
        return None
    return dt_date.fromisoformat(value.strip())


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _detect_mime_type(file_content: bytes, declared_content_type: str | None) -> str:
    """Detect MIME type with fallback when libmagic is unavailable."""
    if magic is not None:
        return str(magic.from_buffer(file_content, mime=True))

    # Fallback to simple file signature checks for common image types.
    if file_content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if file_content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(file_content) >= 12 and file_content[:4] == b"RIFF" and file_content[8:12] == b"WEBP":
        return "image/webp"
    return declared_content_type or "application/octet-stream"


def _admin_emails() -> list[str]:
    return [email.strip() for email in settings.ADMIN_EMAILS.split(",") if email.strip()]


async def _notify_admin_manual_review_needed(*, user_id: str, user_email: str, kyc_id: str) -> None:
    subject = f"[KYC] Manual review required for user {user_id}"
    text_content = (
        "KYC extraction failed and was queued for manual review.\n"
        f"User ID: {user_id}\n"
        f"User Email: {user_email}\n"
        f"KYC ID: {kyc_id}\n"
        "Reason: VPS unreachable or extraction failed after retry."
    )
    html_content = (
        "<p>KYC extraction failed and was queued for manual review.</p>"
        f"<p><strong>User ID:</strong> {user_id}<br>"
        f"<strong>User Email:</strong> {user_email}<br>"
        f"<strong>KYC ID:</strong> {kyc_id}<br>"
        "<strong>Reason:</strong> VPS unreachable or extraction failed after retry.</p>"
    )

    for admin_email in _admin_emails():
        sent = await send_email(admin_email, subject, html_content, text_content)
        if not sent:
            logger.warning(
                "Failed to send KYC manual-review email to %s for kyc_id=%s", admin_email, kyc_id
            )


@router.post("/upload", response_model=KYCUploadResultResponse, status_code=status.HTTP_200_OK)
async def upload_kyc_documents(
    nic_front: UploadFile = File(..., description="NIC front image"),
    nic_back: UploadFile = File(..., description="NIC back image"),
    selfie: UploadFile = File(..., description="Selfie photo"),
    nic_number: str | None = Form(default=None),
    full_name: str | None = Form(default=None),
    date_of_birth: str | None = Form(default=None),
    address: str | None = Form(default=None),
    gender: str | None = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload KYC documents for verification.

    Implements CD-50.1 -> CD-50.11:
    - Multipart upload handling
    - MIME/type and size validation
    - Supabase upload + SHA-256 checksum
    - File integrity records
    - VPS extraction proxy call with timeout/retry
    - Manual-review queueing when VPS fails
    """
    logger.info("KYC upload started for user_id=%s", current_user.id)

    existing_kyc = db.query(KYCDocument).filter(KYCDocument.user_id == current_user.id).first()
    if existing_kyc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"KYC already submitted. Status: {existing_kyc.status}",
        )

    files = {"nic_front": nic_front, "nic_back": nic_back, "selfie": selfie}
    file_contents: dict[str, KYCFilePayload] = {}
    user_provided_data = {
        "nic_number": _clean_optional_text(nic_number),
        "full_name": _clean_optional_text(full_name),
        "date_of_birth": _clean_optional_text(date_of_birth),
        "address": _clean_optional_text(address),
        "gender": _clean_optional_text(gender),
    }

    for file_name, file in files.items():
        content = await file.read()
        await file.seek(0)

        mime_type = _detect_mime_type(content, file.content_type)
        if mime_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{file_name}: Invalid file type. Allowed: JPEG, PNG, WebP. Got: {mime_type}",
            )

        file_size = len(content)
        if file_size > MAX_FILE_SIZE_BYTES:
            file_size_mb = file_size / (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{file_name}: File too large. Max 10MB. Got: {file_size_mb:.2f}MB",
            )

        file_contents[file_name] = {"content": content, "mime_type": mime_type, "size": file_size}
        logger.info(
            "Validated %s for user_id=%s (mime=%s, size_bytes=%s)",
            file_name,
            current_user.id,
            mime_type,
            file_size,
        )

    uploaded_urls: dict[str, str] = {}
    checksums: dict[str, str] = {}
    extension_map = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}

    for file_name, file_data in file_contents.items():
        checksum = hashlib.sha256(file_data["content"]).hexdigest()
        checksums[file_name] = checksum
        extension = extension_map.get(file_data["mime_type"], "jpg")
        file_path = f"{current_user.id}/{file_name}.{extension}"

        try:
            upload_result = await storage.upload_file(
                bucket=settings.SUPABASE_STORAGE_KYC_BUCKET,
                file_path=file_path,
                file_content=file_data["content"],
                content_type=file_data["mime_type"],
            )
            uploaded_urls[file_name] = cast(str, upload_result["url"])
        except Exception as exc:
            logger.exception("Supabase upload failed for %s: %s", file_name, exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload {file_name}: {str(exc)}",
            )

    for file_name, file_data in file_contents.items():
        extension = extension_map.get(file_data["mime_type"], "jpg")
        integrity_record = FileIntegrity(
            file_url=uploaded_urls[file_name],
            file_name=f"{file_name}.{extension}",
            file_size=file_data["size"],
            mime_type=file_data["mime_type"],
            sha256_hash=checksums[file_name],
            uploaded_by=current_user.id,
            verification_status=VerificationStatus.VERIFIED,
        )
        db.add(integrity_record)

    # Needed before creating dependent records in same transaction.
    db.flush()

    # CD-50.8/9: VPS extraction with timeout + retry.
    front_extracted = await extract_nic_with_retry(
        file_contents["nic_front"]["content"],
        side="front",
        content_type=file_contents["nic_front"]["mime_type"],
        max_retries=1,
    )
    back_extracted = await extract_nic_with_retry(
        file_contents["nic_back"]["content"],
        side="back",
        content_type=file_contents["nic_back"]["mime_type"],
        max_retries=1,
    )

    # CD-50.10 queue behavior: mark record for manual admin review when VPS fails.
    manual_review_required = front_extracted is None or back_extracted is None

    # CD-50.11: only extracted JSON is stored in DB (images remain in Supabase).
    extracted_payload: dict[str, object] | None = None
    if not manual_review_required:
        extracted_payload = {
            "front": front_extracted,
            "back": back_extracted,
            "extraction_method": "vps_ollama",
            "extracted_at": datetime.now(UTC).isoformat(),
        }

    kyc_document = KYCDocument(
        user_id=current_user.id,
        nic_number=user_provided_data["nic_number"],
        full_name=user_provided_data["full_name"],
        date_of_birth=_parse_optional_date(user_provided_data["date_of_birth"]),
        address=user_provided_data["address"],
        gender=user_provided_data["gender"],
        nic_front_url=uploaded_urls["nic_front"],
        nic_back_url=uploaded_urls["nic_back"],
        selfie_url=uploaded_urls["selfie"],
        user_provided_data=user_provided_data,
        extracted_data=extracted_payload,
        status=(KYCStatus.PENDING_MANUAL_REVIEW if manual_review_required else KYCStatus.PENDING),
    )

    db.add(kyc_document)
    db.commit()
    db.refresh(kyc_document)

    if manual_review_required:
        try:
            await _notify_admin_manual_review_needed(
                user_id=str(current_user.id),
                user_email=current_user.email,
                kyc_id=str(kyc_document.id),
            )
        except Exception:
            logger.exception(
                "Manual-review notification failed for user_id=%s kyc_id=%s",
                current_user.id,
                kyc_document.id,
            )

    logger.info(
        "KYC upload completed for user_id=%s kyc_id=%s status=%s",
        current_user.id,
        kyc_document.id,
        kyc_document.status.value,
    )
    extraction_success = not manual_review_required
    return {
        "message": "KYC documents uploaded successfully",
        "kyc_id": str(kyc_document.id),
        "status": kyc_document.status.value,
        "extraction_success": extraction_success,
        "needs_manual_review": manual_review_required,
    }


@router.get("/status", response_model=KYCStatusResponse)
async def get_kyc_status(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Check KYC verification status."""
    kyc = db.query(KYCDocument).filter(KYCDocument.user_id == current_user.id).first()
    if not kyc:
        return {
            "has_kyc": False,
            "status": None,
            "submitted_at": None,
            "reviewed_at": None,
            "rejection_reason": None,
            "nic_number": None,
            "full_name": None,
        }

    return {
        "has_kyc": True,
        "status": kyc.status.value,
        "submitted_at": kyc.created_at,
        "reviewed_at": kyc.reviewed_at,
        "rejection_reason": kyc.rejection_reason,
        "nic_number": kyc.nic_number,
        "full_name": kyc.full_name,
    }


@router.get("/my-documents", response_model=KYCUploadResponse)
async def get_my_kyc_documents(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get user's KYC document submission."""
    kyc = db.query(KYCDocument).filter(KYCDocument.user_id == current_user.id).first()
    if not kyc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No KYC submission found")
    return kyc
