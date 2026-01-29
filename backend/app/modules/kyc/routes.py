from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.modules.kyc import models, services
import uuid
import os

router = APIRouter()

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_kyc_document(
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. RUN SECURITY CHECKS
    # We get back the validated content and the hash
    security_data = await services.validate_and_hash_file(file)
    
    # 2. UPLOAD TO SUPABASE (CD-50.5 ✅)
    # Generate a unique filename: user_id/hash.jpg
    # (Using a random UUID for user_id since Auth isn't ready yet)
    test_user_id = uuid.uuid4()
    
    # File name format: secure/uuid/hash.jpg
    file_extension = file.filename.split(".")[-1]
    secure_filename = f"{test_user_id}/{security_data['hash']}.{file_extension}"
    
    # Perform the Upload
    cloud_url = services.upload_file_to_supabase(
        file_content=security_data["content"],
        file_name=secure_filename,
        mime_type=security_data["mime_type"]
    )

    # 3. CREATE DATABASE RECORD
    new_doc = models.KYCDocument(
        user_id=test_user_id,
        status=models.KYCStatus.PENDING
    )

    # Dynamically set the correct URL and HASH
    if document_type == "nic_front":
        new_doc.nic_front_url = cloud_url
        new_doc.nic_front_hash = security_data["hash"]
    elif document_type == "nic_back":
        new_doc.nic_back_url = cloud_url
        new_doc.nic_back_hash = security_data["hash"]
    elif document_type == "selfie":
        new_doc.selfie_url = cloud_url
        new_doc.selfie_hash = security_data["hash"]
    else:
        raise HTTPException(status_code=400, detail="Invalid document_type")

    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    
    return {
        "status": "success", 
        "file_id": new_doc.id, 
        "url": cloud_url,
        "security_hash": security_data["hash"],
        "message": "Securely uploaded to Cloud Storage ☁️"
    }