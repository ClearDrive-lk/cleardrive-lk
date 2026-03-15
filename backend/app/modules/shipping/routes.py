"""Exporter shipping endpoints.

Author: Pavara
Story: CD-72 - Shipping Document Upload
"""

import logging
from datetime import datetime
from typing import cast

from app.core.config import settings
from app.core.database import get_db
from app.core.permissions import Permission, require_permission
from app.core.storage import storage
from app.modules.auth.models import User
from app.modules.orders.models import Order, OrderStatus
from app.modules.orders.state_machine import validate_state_transition
from app.modules.shipping.models import (
    DocumentType,
    ShipmentDetails,
    ShipmentStatus,
    ShippingDocument,
)
from app.modules.shipping.schemas import (
    DocumentListItem,
    DocumentUploadResponse,
    RequiredDocumentsCheck,
    ShippingDetailsResponse,
    ShippingDetailsSubmit,
)
from app.services.orders.status_history import status_history_service
from app.services.security.file_integrity import file_integrity_service
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/shipping", tags=["shipping"])
logger = logging.getLogger(__name__)

# --- Constants ---

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
}


# --- Helpers ---


def _get_shipment_for_exporter(
    order_id: str,
    current_user: User,
    db: Session,
) -> ShipmentDetails:
    """Fetch shipment and verify the current user is the assigned exporter."""
    shipment = db.query(ShipmentDetails).filter(ShipmentDetails.order_id == order_id).first()
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment for order {order_id} not found.",
        )
    if shipment.exporter_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the assigned exporter can manage documents for this shipment.",
        )
    return shipment


def _missing_required_docs(shipment: ShipmentDetails) -> list[str]:
    """Return labels of required document types not yet uploaded."""
    uploaded = {doc.document_type for doc in shipment.documents}

    missing: list[str] = []
    if DocumentType.BILL_OF_LADING not in uploaded and DocumentType.BILL_OF_LANDING not in uploaded:
        missing.append("BILL_OF_LADING")
    if DocumentType.COMMERCIAL_INVOICE not in uploaded:
        missing.append("COMMERCIAL_INVOICE")
    if DocumentType.PACKING_LIST not in uploaded:
        missing.append("PACKING_LIST")
    if DocumentType.EXPORT_CERTIFICATE not in uploaded:
        missing.append("EXPORT_CERTIFICATE")
    return missing


def _mark_submitted_if_ready(shipment: ShipmentDetails) -> None:
    """Stamp submission time once shipment details and required docs are both present."""
    has_details = all(
        [
            shipment.vessel_name,
            shipment.vessel_registration,
            shipment.voyage_number,
            shipment.departure_port,
            shipment.arrival_port,
            shipment.departure_date,
            shipment.estimated_arrival_date,
            shipment.container_number,
            shipment.bill_of_landing_number,
            shipment.seal_number,
            shipment.tracking_number,
        ]
    )

    if has_details and shipment.documents_uploaded:
        if shipment.submitted_at is None:
            shipment.submitted_at = datetime.utcnow()
        shipment.status = ShipmentStatus.AWAITING_ADMIN_APPROVAL


# CD-71: Submit shipping details


@router.post("/{order_id}/details", response_model=ShippingDetailsResponse)
async def submit_shipping_details(
    order_id: str,
    payload: ShippingDetailsSubmit,
    current_user: User = Depends(require_permission(Permission.UPDATE_SHIPPING_DETAILS)),
    db: Session = Depends(get_db),
):
    """
    Submit shipping details for an assigned order (Exporter only).

    **Story**: CD-71
    """
    shipment = _get_shipment_for_exporter(order_id, current_user, db)

    shipment.vessel_name = payload.vessel_name
    shipment.vessel_registration = payload.vessel_registration
    shipment.voyage_number = payload.voyage_number
    shipment.departure_port = payload.departure_port
    shipment.arrival_port = payload.arrival_port
    shipment.departure_date = payload.departure_date
    shipment.container_number = payload.container_number
    shipment.bill_of_landing_number = payload.bill_of_landing_number
    shipment.seal_number = payload.seal_number
    shipment.tracking_number = payload.tracking_number

    shipment.estimated_arrival_date = payload.estimated_arrival_date

    # Update shipment status to reflect submitted details
    if shipment.status == ShipmentStatus.PENDING_SHIPMENT:
        shipment.status = ShipmentStatus.AWAITING_ADMIN_APPROVAL

    _mark_submitted_if_ready(shipment)

    # Update order status to awaiting shipment confirmation
    order = db.query(Order).filter(Order.id == shipment.order_id).first()
    if order is not None and order.status != OrderStatus.AWAITING_SHIPMENT_CONFIRMATION:
        is_valid, error_message = validate_state_transition(
            order=order,
            new_status=OrderStatus.AWAITING_SHIPMENT_CONFIRMATION,
            db=db,
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message,
            )
        old_status = order.status
        order.status = OrderStatus.AWAITING_SHIPMENT_CONFIRMATION
        status_history_service.create_history_entry(
            db=db,
            order=order,
            from_status=old_status,
            to_status=OrderStatus.AWAITING_SHIPMENT_CONFIRMATION,
            changed_by=current_user,
            notes="Shipping details submitted by exporter",
        )

    db.commit()
    db.refresh(shipment)

    logger.info(
        "Shipping details submitted order_id=%s exporter_id=%s",
        order_id,
        current_user.id,
    )
    return shipment


@router.get("/{order_id}/details", response_model=ShippingDetailsResponse)
async def get_shipping_details(
    order_id: str,
    current_user: User = Depends(require_permission(Permission.UPDATE_SHIPPING_DETAILS)),
    db: Session = Depends(get_db),
):
    """Get shipping details for an order (Exporter only)."""
    shipment = _get_shipment_for_exporter(order_id, current_user, db)
    return shipment


# CD-72.1: Upload document


@router.post(
    "/{order_id}/documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_shipping_document(
    order_id: str,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission(Permission.UPLOAD_SHIPMENT_DOCUMENTS)),
    db: Session = Depends(get_db),
):
    """
    Upload a shipping document (Exporter only).

    **Story**: CD-72.1

    **Document Types** (CD-72.2):
    - BILL_OF_LADING (Required)
    - COMMERCIAL_INVOICE (Required)
    - PACKING_LIST (Required)
    - EXPORT_CERTIFICATE (Required)
    - CERTIFICATE_OF_ORIGIN (Optional)
    - CONTAINER_PHOTO (Optional)
    - OTHER (Optional)

    **Validations** (CD-72.3):
    - MIME type: PDF or images only
    - File size: Max 10 MB
    - Document type: Must be valid enum

    **Security** (CD-72.4):
    - SHA-256 hash stored on document record
    - FileIntegrity record created (CD-53 integration)
    """

    logger.info(
        "Shipping document upload order_id=%s type=%s file=%s exporter=%s",
        order_id,
        document_type,
        file.filename,
        current_user.email,
    )

    # 1. Shipment & access
    shipment = _get_shipment_for_exporter(order_id, current_user, db)

    # 2. Validate document type (CD-72.2)
    try:
        doc_type = DocumentType(document_type)
    except ValueError:
        valid = ", ".join(t.value for t in DocumentType)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document type '{document_type}'. Valid types: {valid}",
        )

    # 3. Read file content
    content = await file.read()

    # 4. Validate MIME type (CD-72.3)
    mime_type = file.content_type or "application/octet-stream"
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{mime_type}'. Allowed: PDF, JPEG, PNG, WebP",
        )

    # 5. Validate file size (CD-72.3)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large ({len(content) / (1024 * 1024):.1f} MB). Maximum size: 10 MB",
        )

    # 6. SHA-256 integrity hash (CD-72.4)
    sha256_hash = file_integrity_service.calculate_sha256(content)
    logger.debug("SHA-256 computed hash_prefix=%s", sha256_hash[:16])

    # 7. Upload to Supabase storage
    storage_path = f"shipping/{order_id}/{doc_type.value}/{file.filename}"
    try:
        upload_result = await storage.upload_file(
            bucket=settings.SUPABASE_STORAGE_SHIPPING_BUCKET,
            file_path=storage_path,
            file_content=content,
            content_type=mime_type,
        )
        file_url = cast(str, upload_result["url"])
    except Exception as exc:
        logger.exception("Storage upload failed order_id=%s doc_type=%s", order_id, doc_type)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File storage failed. Please try again.",
        ) from exc

    # 8. Remove previous upload of same type (replace semantics)
    existing = (
        db.query(ShippingDocument)
        .filter(
            ShippingDocument.shipment_id == shipment.id,
            ShippingDocument.document_type == doc_type,
        )
        .first()
    )
    if existing:
        db.delete(existing)
        db.flush()

    # 9. Persist document record with sha256_hash (CD-72.4)
    doc = ShippingDocument(
        shipment_id=shipment.id,
        document_type=doc_type,
        file_name=file.filename or f"{doc_type.value}.bin",
        file_url=file_url,
        file_size=len(content),
        mime_type=mime_type,
        sha256_hash=sha256_hash,
        uploaded_by=current_user.id,
    )
    db.add(doc)

    # 10. Create FileIntegrity record (CD-53 integration)
    try:
        file_integrity_service.create_integrity_record(
            db=db,
            file_url=file_url,
            file_name=file.filename or f"{doc_type.value}.bin",
            file_bytes=content,
            mime_type=mime_type,
            uploaded_by_id=str(current_user.id),
        )
        logger.info("FileIntegrity record created order_id=%s", order_id)
    except Exception as exc:
        # Don't fail the upload if integrity record creation fails
        logger.warning("FileIntegrity record creation failed order_id=%s: %s", order_id, exc)

    # 11. Update shipment status if first upload
    if shipment.status == ShipmentStatus.PENDING_SHIPMENT:
        shipment.status = ShipmentStatus.DOCS_UPLOADED

    # 12. Check if all required docs present (CD-72.5)
    db.flush()
    db.refresh(shipment)
    missing = _missing_required_docs(shipment)
    if not missing:
        shipment.documents_uploaded = True
        _mark_submitted_if_ready(shipment)
        logger.info(
            "All required documents uploaded - order_id=%s awaiting admin approval",
            order_id,
        )
    else:
        logger.info("Missing documents order_id=%s missing=%s", order_id, ", ".join(missing))

    db.commit()
    db.refresh(doc)

    logger.info(
        "Document uploaded order_id=%s type=%s file=%s hash=%s",
        order_id,
        doc_type.value,
        file.filename,
        sha256_hash[:12],
    )

    return DocumentUploadResponse(
        id=doc.id,
        shipment_id=doc.shipment_id,
        order_id=shipment.order_id,
        document_type=doc.document_type.value,
        file_name=doc.file_name,
        file_size=doc.file_size,
        mime_type=doc.mime_type,
        file_url=doc.file_url,
        verified=doc.verified,
        uploaded_at=doc.uploaded_at,
        uploaded_by=doc.uploaded_by,
    )


# CD-72: List documents


@router.get("/{order_id}/documents", response_model=list[DocumentListItem])
async def list_shipping_documents(
    order_id: str,
    current_user: User = Depends(require_permission(Permission.UPLOAD_SHIPMENT_DOCUMENTS)),
    db: Session = Depends(get_db),
):
    """
    List all uploaded documents for a shipment (Exporter only).

    **Story**: CD-72
    """
    shipment = _get_shipment_for_exporter(order_id, current_user, db)

    return [
        DocumentListItem(
            id=doc.id,
            shipment_id=doc.shipment_id,
            order_id=shipment.order_id,
            document_type=doc.document_type.value,
            file_name=doc.file_name,
            file_size=doc.file_size or 0,
            mime_type=doc.mime_type or "",
            file_url=doc.file_url,
            verified=doc.verified,
            uploaded_at=doc.uploaded_at,
            uploaded_by=doc.uploaded_by,
        )
        for doc in shipment.documents
    ]


# CD-72.5: Required documents check


@router.get("/{order_id}/documents/check", response_model=RequiredDocumentsCheck)
async def check_required_documents(
    order_id: str,
    current_user: User = Depends(require_permission(Permission.UPLOAD_SHIPMENT_DOCUMENTS)),
    db: Session = Depends(get_db),
):
    """
    Check whether all required documents have been uploaded.

    **Story**: CD-72.5

    Required:
    - BILL_OF_LADING
    - COMMERCIAL_INVOICE
    - PACKING_LIST
    - EXPORT_CERTIFICATE
    """
    shipment = _get_shipment_for_exporter(order_id, current_user, db)

    uploaded_types = [doc.document_type.value for doc in shipment.documents]
    missing = _missing_required_docs(shipment)
    required_labels = [
        "BILL_OF_LADING",
        "COMMERCIAL_INVOICE",
        "PACKING_LIST",
        "EXPORT_CERTIFICATE",
    ]
    total_required = len(required_labels)
    total_uploaded = total_required - len(missing)
    pct = int((total_uploaded / total_required) * 100) if total_required else 100

    return RequiredDocumentsCheck(
        order_id=shipment.order_id,
        total_required=total_required,
        total_uploaded=total_uploaded,
        all_uploaded=len(missing) == 0,
        uploaded_documents=uploaded_types,
        missing_documents=missing,
        completion_percentage=pct,
    )
