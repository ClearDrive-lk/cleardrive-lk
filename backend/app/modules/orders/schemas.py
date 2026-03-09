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


class OrderListItem(BaseModel):
    """Lightweight order summary for dashboard lists."""

    id: UUID
    user_id: UUID
    vehicle_id: UUID
    status: str
    payment_status: str
    total_cost_lkr: Decimal | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderStatusHistoryResponse(BaseModel):
    """
    Order status history item.

    Story: CD-32.2
    """

    id: UUID
    order_id: UUID
    from_status: Optional[str]
    to_status: str
    notes: Optional[str]

    # Who changed it
    changed_by_id: UUID | None
    changed_by_name: str
    changed_by_email: str

    # When
    created_at: datetime

    class Config:
        from_attributes = True


class OrderTimelineResponse(BaseModel):
    """
    Complete order timeline.

    Story: CD-32.2
    """

    order_id: UUID
    current_status: str
    created_at: datetime
    total_events: int
    timeline: list[OrderStatusHistoryResponse]

    class Config:
        from_attributes = True
