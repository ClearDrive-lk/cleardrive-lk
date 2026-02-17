from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OrderBase(BaseModel):
    vehicle_id: UUID
    shipping_address: str
    phone: str


class OrderCreate(OrderBase):
    """Schema for creating an order."""

    pass


# 1. Inspection data schema
class InspectionData(BaseModel):
    status: str
    notes: Optional[str] = None
    images: List[str] = []
    date: datetime


# 2. CD30 order creation schema
class CD30OrderCreate(BaseModel):
    vehicle_id: UUID
    shipping_address: str
    phone: str
    inspection_data: InspectionData


# 3. Order response with inspection fields
class OrderResponse(OrderBase):
    """Schema for order response."""

    id: UUID
    status: str
    payment_status: str
    user_id: UUID

    # Inspection fields
    total_cost_lkr: Decimal | None
    inspection_status: Optional[str] = None
    inspector_notes: Optional[str] = None
    inspection_images: Optional[List[str]] = None
    inspection_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
