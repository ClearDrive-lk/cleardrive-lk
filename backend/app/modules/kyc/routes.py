# backend/app/modules/kyc/routes.py

"""
KYC document upload endpoint.
Author: Pavara
Story: CD-50 - KYC Document Upload
"""

import hashlib

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.storage import storage
from app.modules.auth.models import User
from app.modules.kyc.models import KYCDocument, KYCStatus
from app.modules.kyc.schemas import KYCStatusResponse, KYCUploadResponse
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

try:
    import magic
except ImportError:  # pragma: no cover
    magic = None

router = APIRouter(prefix="/kyc", tags=["kyc"])


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


# ===================================================================
# ENDPOINT: UPLOAD KYC DOCUMENTS (CD-50.1)
# ===================================================================


@router.post("/upload", response_model=KYCUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_kyc_documents(
    nic_front: UploadFile = File(..., description="NIC front image"),
    nic_back: UploadFile = File(..., description="NIC back image"),
    selfie: UploadFile = File(..., description="Selfie photo"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload KYC documents for verification.

    **Story**: CD-50 - KYC Document Upload

    **Required Files:**
    1. nic_front: Front side of National Identity Card
    2. nic_back: Back side of National Identity Card
    3. selfie: Photo of user holding NIC

    **Validations:**
    - File type: JPEG, PNG, or WebP only (CD-50.3)
    - File size: Maximum 10MB per file (CD-50.4)
    - One submission per user

    **Process:**
    1. Check if user already submitted KYC
    2. Validate file types (CD-50.3)
    3. Validate file sizes (CD-50.4)
    4. Upload to Supabase Storage (CD-50.5)
    5. Calculate SHA-256 checksums (CD-50.6)
    6. Store file integrity records (CD-50.7)
    7. Create KYC document record
    8. Return uploaded document details

    **Returns:**
    - KYC document with PENDING status
    - Document URLs
    - Extracted data (populated by Claude API later)
    """

    print("\n" + "=" * 70)
    print("KYC UPLOAD STARTED")
    print(f"   User: {current_user.email}")
    print("=" * 70 + "\n")

    # ===============================================================
    # STEP 1: CHECK IF USER ALREADY SUBMITTED KYC
    # ===============================================================
    existing_kyc = db.query(KYCDocument).filter(KYCDocument.user_id == current_user.id).first()

    if existing_kyc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"KYC already submitted. Status: {existing_kyc.status}",
        )

    print("STEP 1: No existing KYC found")

    # ===============================================================
    # STEP 2: VALIDATE FILE TYPES (CD-50.3)
    # ===============================================================

    files = {"nic_front": nic_front, "nic_back": nic_back, "selfie": selfie}

    allowed_mime_types = ["image/jpeg", "image/png", "image/webp"]

    file_contents = {}

    for file_name, file in files.items():
        # Read file content
        content = await file.read()
        await file.seek(0)  # Reset file pointer

        # Validate MIME type using python-magic when available.
        mime_type = _detect_mime_type(content, file.content_type)

        if mime_type not in allowed_mime_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{file_name}: Invalid file type. Allowed: JPEG, PNG, WebP. Got: {mime_type}",
            )

        # Validate file size (10MB = 10 * 1024 * 1024 bytes) (CD-50.4)
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

        print(f"âœ… STEP 2: {file_name} validated")
        print(f"   Type: {mime_type}")
        print(f"   Size: {file_size_mb:.2f} MB")

    # ===============================================================
    # STEP 3: UPLOAD TO SUPABASE STORAGE (CD-50.5)
    # ===============================================================

    uploaded_urls = {}
    checksums = {}

    for file_name, file_data in file_contents.items():
        # Calculate SHA-256 checksum (CD-50.6)
        checksum = hashlib.sha256(file_data["content"]).hexdigest()
        checksums[file_name] = checksum

        # Determine file extension from MIME type
        extension_map = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
        extension = extension_map.get(file_data["mime_type"], "jpg")

        # Upload to Supabase Storage
        # Path: kyc-documents/{user_id}/{file_name}.{extension}
        file_path = f"{current_user.id}/{file_name}.{extension}"

        try:
            upload_result = await storage.upload_file(
                bucket="kyc-documents",
                file_path=file_path,
                file_content=file_data["content"],
                content_type=file_data["mime_type"],
            )

            uploaded_urls[file_name] = upload_result["url"]

            print(f"âœ… STEP 3: {file_name} uploaded to Supabase")
            print(f"   URL: {upload_result['url'][:50]}...")
            print(f"   Checksum: {checksum[:16]}...")

        except Exception as e:
            print(f"âŒ Upload failed for {file_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload {file_name}: {str(e)}",
            )

    # ===============================================================
    # STEP 4: STORE FILE INTEGRITY RECORDS (CD-50.7)
    # ===============================================================

    # Note: File integrity will be stored by Kalidu's security module
    # For now, we'll just log the checksums

    print("\nSTEP 4: File integrity checksums calculated")
    for file_name, checksum in checksums.items():
        print(f"   {file_name}: {checksum}")

    # TODO: Store in file_integrity table when security module is ready
    # from app.modules.security.models import FileIntegrity
    #
    # for file_name, checksum in checksums.items():
    #     integrity_record = FileIntegrity(
    #         file_url=uploaded_urls[file_name],
    #         sha256_hash=checksum,
    #         file_size=file_contents[file_name]["size"],
    #         mime_type=file_contents[file_name]["mime_type"],
    #         uploaded_by=current_user.id
    #     )
    #     db.add(integrity_record)

    # ===============================================================
    # STEP 5: CREATE KYC DOCUMENT RECORD
    # ===============================================================

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

    print("\nSTEP 5: KYC document record created")
    print(f"   ID: {kyc_document.id}")
    print(f"   Status: {kyc_document.status.value}")

    print("\n" + "=" * 70)
    print("KYC UPLOAD COMPLETED")
    print(f"   Document ID: {kyc_document.id}")
    print("   Status: PENDING")
    print("   Next: Claude API will extract NIC data")
    print("=" * 70 + "\n")

    # Note: Claude API extraction will happen in CD-51

    return kyc_document


# ===================================================================
# ENDPOINT: GET KYC STATUS
# ===================================================================


@router.get("/status", response_model=KYCStatusResponse)
async def get_kyc_status(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Check KYC verification status.

    **Returns:**
    - has_kyc: Boolean indicating if KYC submitted
    - status: PENDING, APPROVED, or REJECTED
    - submission and review timestamps
    - rejection reason (if rejected)
    """

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


# ===================================================================
# ENDPOINT: GET KYC DOCUMENTS (for user to view their submission)
# ===================================================================


@router.get("/my-documents", response_model=KYCUploadResponse)
async def get_my_kyc_documents(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get user's KYC document submission.

    **Returns:**
    - Full KYC document details
    - Document URLs
    - Extracted data
    - Verification status
    """

    kyc = db.query(KYCDocument).filter(KYCDocument.user_id == current_user.id).first()

    if not kyc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No KYC submission found")

    return kyc
