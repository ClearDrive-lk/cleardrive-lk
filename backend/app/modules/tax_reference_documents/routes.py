from __future__ import annotations

import re
import uuid
from datetime import datetime

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.core.storage import storage
from app.models.tax_reference_document import TaxReferenceDocument
from app.modules.auth.models import User
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter(tags=["Tax Reference Documents"])


class TaxReferenceDocumentResponse(BaseModel):
    id: str
    title: str
    issued_label: str
    document_type: str | None = None
    description: str | None = None
    file_name: str
    file_url: str
    mime_type: str
    display_order: int
    is_active: bool
    created_at: datetime


def _serialize(document: TaxReferenceDocument) -> TaxReferenceDocumentResponse:
    return TaxReferenceDocumentResponse(
        id=str(document.id),
        title=document.title,
        issued_label=document.issued_label,
        document_type=document.document_type,
        description=document.description,
        file_name=document.file_name,
        file_url=document.file_url,
        mime_type=document.mime_type,
        display_order=document.display_order,
        is_active=document.is_active,
        created_at=document.created_at,
    )


def _slugify(value: str) -> str:
    sanitized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return sanitized or "document"


async def _upload_reference_pdf(*, file_path: str, content: bytes, content_type: str) -> dict:
    preferred_buckets = [
        settings.SUPABASE_STORAGE_REFERENCE_BUCKET,
        settings.SUPABASE_STORAGE_SHIPPING_BUCKET,
        settings.SUPABASE_STORAGE_KYC_BUCKET,
    ]
    seen: set[str] = set()
    last_error: Exception | None = None

    for bucket in preferred_buckets:
        if not bucket or bucket in seen:
            continue
        seen.add(bucket)
        try:
            return await storage.upload_file(
                bucket=bucket,
                file_path=file_path,
                file_content=content,
                content_type=content_type,
            )
        except Exception as exc:
            last_error = exc
            if "Bucket not found" not in str(exc):
                break

    if last_error is not None:
        raise last_error
    raise RuntimeError("No storage bucket configured for tax reference documents.")


@router.get("/tax-reference-documents", response_model=list[TaxReferenceDocumentResponse])
async def list_public_tax_reference_documents(db: Session = Depends(get_db)):
    documents = (
        db.query(TaxReferenceDocument)
        .filter(TaxReferenceDocument.is_active.is_(True))
        .order_by(TaxReferenceDocument.display_order.asc(), TaxReferenceDocument.created_at.desc())
        .all()
    )
    return [_serialize(document) for document in documents]


@router.get(
    "/admin/tax-reference-documents",
    response_model=list[TaxReferenceDocumentResponse],
)
async def list_admin_tax_reference_documents(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    documents = (
        db.query(TaxReferenceDocument)
        .order_by(TaxReferenceDocument.display_order.asc(), TaxReferenceDocument.created_at.desc())
        .all()
    )
    return [_serialize(document) for document in documents]


@router.post(
    "/admin/tax-reference-documents",
    response_model=TaxReferenceDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_tax_reference_document(
    title: str = Form(...),
    issued_label: str = Form(...),
    document_type: str | None = Form(None),
    description: str | None = Form(None),
    display_order: int = Form(0),
    is_active: bool = Form(True),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF reference documents are supported.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty."
        )

    safe_title = _slugify(title)
    file_path = f"tax-reference-docs/{safe_title}-{uuid.uuid4().hex}.pdf"
    try:
        upload_result = await _upload_reference_pdf(
            file_path=file_path,
            content=content,
            content_type=file.content_type or "application/pdf",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reference document upload failed: {str(exc)}",
        ) from exc

    document = TaxReferenceDocument(
        title=title.strip(),
        issued_label=issued_label.strip(),
        document_type=document_type.strip() if document_type else None,
        description=description.strip() if description else None,
        file_name=file.filename,
        file_url=str(upload_result["url"]),
        mime_type=file.content_type or "application/pdf",
        display_order=display_order,
        is_active=is_active,
        created_by=current_admin.id,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return _serialize(document)


@router.patch(
    "/admin/tax-reference-documents/{document_id}",
    response_model=TaxReferenceDocumentResponse,
)
async def update_tax_reference_document(
    document_id: uuid.UUID,
    title: str = Form(...),
    issued_label: str = Form(...),
    document_type: str | None = Form(None),
    description: str | None = Form(None),
    display_order: int = Form(0),
    is_active: bool = Form(True),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    document = db.query(TaxReferenceDocument).filter(TaxReferenceDocument.id == document_id).first()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    document.title = title.strip()
    document.issued_label = issued_label.strip()
    document.document_type = document_type.strip() if document_type else None
    document.description = description.strip() if description else None
    document.display_order = display_order
    document.is_active = is_active
    db.commit()
    db.refresh(document)
    return _serialize(document)


@router.delete(
    "/admin/tax-reference-documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_tax_reference_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    document = db.query(TaxReferenceDocument).filter(TaxReferenceDocument.id == document_id).first()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    db.delete(document)
    db.commit()
    return None
