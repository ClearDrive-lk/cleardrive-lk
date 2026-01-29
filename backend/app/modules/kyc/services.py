import hashlib
import magic # pip install python-magic
from fastapi import UploadFile, HTTPException
from supabase import create_client, Client
from app.core.config import settings

# Initialize Supabase Client using credentials from .env
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
BUCKET_NAME = "kyc_documents"

async def validate_and_hash_file(file: UploadFile):
    """
    Security Gatekeeper: Checks Size, Type, and Integrity.
    """
    content = await file.read()
    await file.seek(0) # Reset cursor
    
    # 1. CHECK SIZE (10MB)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (Max 10MB)")

    # 2. MAGIC NUMBER CHECK (Real File Type)
    mime_type = magic.from_buffer(content, mime=True)
    allowed_types = ["image/jpeg", "image/png", "application/pdf"]
    
    if mime_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type: {mime_type}. Only JPEG, PNG, or PDF allowed."
        )

    # 3. GENERATE HASH
    sha256_hash = hashlib.sha256(content).hexdigest()
    
    return {
        "hash": sha256_hash,
        "mime_type": mime_type,
        "content": content # Return content so we can upload it
    }

def upload_file_to_supabase(file_content: bytes, file_name: str, mime_type: str) -> str:
    """
    Uploads bytes to Supabase and returns the Public URL.
    """
    try:
        # Upload to Supabase Storage
        supabase.storage.from_(BUCKET_NAME).upload(
            path=file_name,
            file=file_content,
            file_options={"content-type": mime_type}
        )
        
        # Get the Public URL so the frontend can display it later
        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_name)
        return public_url
        
    except Exception as e:
        print(f"Supabase Upload Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload to Cloud Storage")