# backend/app/modules/kyc/routes.py

"""KYC document upload endpoints."""

from __future__ import annotations

import hashlib

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.storage import storage
from app.modules.auth.models import User
from app.modules.kyc.models import KYCDocument, KYCStatus
from app.modules.kyc.schemas import KYCStatusResponse, KYCUploadResponse
from app.modules.security.models import FileIntegrity, VerificationStatus
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

try:
    import magic
except ImportError:  # pragma: no cover - platform-specific optional dependency
    magic = None


router = APIRouter(prefix="/kyc", tags=["kyc"])


@router.post("/upload", response_model=KYCUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_kyc_documents(
    nic_front: UploadFile = File(..., description="NIC front image"),
    nic_back: UploadFile = File(..., description="NIC back image"),
    selfie: UploadFile = File(..., description="Selfie photo"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload KYC documents with validation and integrity tracking."""
    existing_kyc = db.query(KYCDocument).filter(KYCDocument.user_id == current_user.id).first()
    if existing_kyc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"KYC already submitted. Status: {existing_kyc.status}",
        )

    files = {"nic_front": nic_front, "nic_back": nic_back, "selfie": selfie}
    allowed_mime_types = {"image/jpeg", "image/png", "image/webp"}
    file_contents: dict[str, dict[str, object]] = {}

    for file_name, file in files.items():
        content = await file.read()
        await file.seek(0)

        if magic is not None:
            mime_type = magic.from_buffer(content, mime=True)
        else:
            mime_type = file.content_type or "application/octet-stream"

        if mime_type not in allowed_mime_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{file_name}: Invalid file type. Allowed: JPEG, PNG, WebP. Got: {mime_type}",
            )

        file_size_mb = len(content) / (1024 * 1024)
        if file_size_mb > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{file_name}: File too large. Max 10MB. Got: {file_size_mb:.2f}MB",
            )

        file_contents[file_name] = {
            "content": content,
            "mime_type": mime_type,
            "size": len(content),
        }

    uploaded_urls: dict[str, str] = {}
    checksums: dict[str, str] = {}

    extension_map = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
    for file_name, file_data in file_contents.items():
        content = file_data["content"]
        mime_type = str(file_data["mime_type"])
        if not isinstance(content, bytes):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Invalid in-memory content type for {file_name}",
            )
        checksum = hashlib.sha256(content).hexdigest()
        checksums[file_name] = checksum
        extension = extension_map.get(mime_type, "jpg")
        file_path = f"{current_user.id}/{file_name}.{extension}"

        try:
            upload_result = await storage.upload_file(
                bucket="kyc-documents",
                file_path=file_path,
                file_content=content,
                content_type=mime_type,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload {file_name}: {exc}",
            ) from exc

        uploaded_urls[file_name] = upload_result["url"]

    for file_name, file_data in file_contents.items():
        size_value = file_data["size"]
        if not isinstance(size_value, int):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Invalid file size value for {file_name}",
            )
        db.add(
            FileIntegrity(
                file_url=uploaded_urls[file_name],
                sha256_hash=checksums[file_name],
                file_size=size_value,
                mime_type=str(file_data["mime_type"]),
                uploaded_by=current_user.id,
                verification_status=VerificationStatus.VERIFIED,
            )
        )

    db.flush()
    kyc_document = KYCDocument(
        user_id=current_user.id,
        nic_front_url=uploaded_urls["nic_front"],
        nic_back_url=uploaded_urls["nic_back"],
        selfie_url=uploaded_urls["selfie"],
        status=KYCStatus.PENDING,
    )
    db.add(kyc_document)
    db.commit()
    db.refresh(kyc_document)
    return kyc_document


@router.get("/status", response_model=KYCStatusResponse)
async def get_kyc_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user's KYC status."""
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user's submitted KYC document."""
    kyc = db.query(KYCDocument).filter(KYCDocument.user_id == current_user.id).first()
    if not kyc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No KYC submission found")
    return kyc
