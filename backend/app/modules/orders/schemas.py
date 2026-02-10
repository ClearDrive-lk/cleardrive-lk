# backend/app/modules/orders/schemas.py

"""
Order Pydantic schemas.
Author: Tharin
Epic: CD-E4
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class OrderCreate(BaseModel):
    """Schema for creating a new order."""
    
    vehicle_id: UUID
    shipping_address: str = Field(..., min_length=10, max_length=500)
    phone: str = Field(..., pattern=r"^0\d{9}$")  # Sri Lankan phone: 0XXXXXXXXX
    
    @field_validator('phone')
    def validate_phone(cls, v):
        """Validate Sri Lankan phone number."""
        if not v.startswith('0') or len(v) != 10:
            raise ValueError('Phone must be 10 digits starting with 0')
        return v


class CostBreakdown(BaseModel):
    """Cost breakdown for an order."""
    
    vehicle_cost_lkr: Decimal
    shipping_cost_lkr: Decimal
    customs_duty_lkr: Decimal
    vat_lkr: Decimal
    total_cost_lkr: Decimal


class OrderResponse(BaseModel):
    """Schema for order response."""
    
    id: UUID
    user_id: UUID
    vehicle_id: UUID
    status: str
    payment_status: str
    shipping_address: str
    phone: str
    vehicle_cost_lkr: Decimal
    shipping_cost_lkr: Decimal
    customs_duty_lkr: Decimal
    vat_lkr: Decimal
    total_cost_lkr: Decimal
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """List of orders with pagination."""
    
    orders: List[OrderResponse]
    pagination: dict


class OrderStatusUpdate(BaseModel):
    """Schema for updating order status."""
    
    new_status: str
    notes: Optional[str] = None


class OrderTimelineItem(BaseModel):
    """Single timeline item."""
    
    old_status: Optional[str]
    new_status: str
    changed_by: Optional[UUID]
    changed_at: datetime
    notes: Optional[str]


class OrderTimelineResponse(BaseModel):
    """Order timeline (status history)."""
    
    order_id: UUID
    current_status: str
    timeline: List[OrderTimelineItem]