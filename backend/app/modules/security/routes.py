from __future__ import annotations

from app.core.database import get_db
from app.core.permissions import Permission, require_permission
from app.modules.auth.models import User
from app.modules.security.models import FileIntegrity
from app.services.security.file_integrity import file_integrity_service
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/security", tags=["security"])


@router.post("/verify-file/{file_integrity_id}")
async def verify_file_integrity_record(
    file_integrity_id: str,
    _: User = Depends(require_permission(Permission.VERIFY_FILE_INTEGRITY)),
    db: Session = Depends(get_db),
):
    integrity = db.query(FileIntegrity).filter(FileIntegrity.id == file_integrity_id).first()
    if integrity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File integrity record not found"
        )

    is_valid, error = file_integrity_service.verify_record(db, integrity)
    if is_valid:
        return {
            "is_valid": True,
            "message": "File integrity verified successfully",
            "file_name": integrity.file_name,
            "last_verified_at": (
                integrity.last_verified.isoformat() if integrity.last_verified else None
            ),
        }

    return {
        "is_valid": False,
        "message": f"Verification failed: {error}",
        "file_name": integrity.file_name,
        "error": error,
    }


@router.post("/verify-all-files")
async def verify_all_files(
    _: User = Depends(require_permission(Permission.VERIFY_FILE_INTEGRITY)),
    db: Session = Depends(get_db),
):
    stats = file_integrity_service.verify_all_files(db)
    return {"message": "File verification completed", "statistics": stats}


@router.get("/tampering-alerts")
async def get_tampering_alerts(
    _: User = Depends(require_permission(Permission.MANAGE_SECURITY_EVENTS)),
    db: Session = Depends(get_db),
):
    tampered_files = (
        db.query(FileIntegrity)
        .filter(FileIntegrity.tampering_detected.is_(True))
        .order_by(FileIntegrity.tampering_detected_at.desc())
        .all()
    )

    return {
        "total_alerts": len(tampered_files),
        "alerts": [
            {
                "id": str(file.id),
                "file_name": file.file_name,
                "file_url": file.file_url,
                "uploaded_by": str(file.uploaded_by) if file.uploaded_by else None,
                "detected_at": (
                    file.tampering_detected_at.isoformat() if file.tampering_detected_at else None
                ),
                "stored_hash": file.sha256_hash,
                "verification_error": file.verification_error,
            }
            for file in tampered_files
        ],
    }
