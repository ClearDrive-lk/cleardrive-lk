from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.shipping.enums import DocumentType
from app.modules.shipping.schemas.documents import ShippingDocumentResponse
from app.modules.shipping.document_validator import DocumentValidator

router = APIRouter(prefix="/api/v1/shipping", tags=["Shipping Documents"])

@router.post("/orders/{order_id}/documents", response_model=ShippingDocumentResponse)
async def upload_shipping_document(
    order_id: int,
    document_type: DocumentType = Form(...),   # CD-322
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # CD-323 (MIME + size validation)
    try:
        mime_type, file_size = await DocumentValidator.validate_mime_and_size(file)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # For now return metadata (later you'll store to DB + Supabase)
    return {
        "document_type": document_type.value,
        "filename": file.filename,
        "mime_type": mime_type,
        "file_size": file_size,
    }
