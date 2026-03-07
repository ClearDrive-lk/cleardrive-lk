from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OrderBase(BaseModel):
    vehicle_id: UUID
    shipping_address: str
    phone: str


class OrderCreate(OrderBase):
    """Schema for creating an order."""

    pass


class OrderResponse(OrderBase):
    """Schema for order response."""

    id: UUID
    status: str
    payment_status: str
    user_id: UUID

    model_config = ConfigDict(from_attributes=True)
