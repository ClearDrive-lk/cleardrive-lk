from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ShippingDocumentResponse(BaseModel):
    id: int
    order_id: int
    document_type: str
    filename: str
    file_url: str
    mime_type: str
    file_size: int
    sha256: str
    created_at: datetime
