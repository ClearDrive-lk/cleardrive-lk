# backend/app/api/v1/payments.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.payments.models import Payment, PaymentStatus, PaymentIdempotency
from app.modules.orders.models import Order
from pydantic import BaseModel, Field
from datetime import datetime
import hashlib
import secrets
import os
from decimal import Decimal
from typing import Optional
import json

router = APIRouter(prefix="/payments", tags=["payments"])



# Pydantic Schemas (Request/Response models)

class PaymentInitiateRequest(BaseModel):
    """Request to initiate a payment."""
    order_id: str = Field(..., description="Order ID to pay for")


class PaymentInitiateResponse(BaseModel):
    """Response from payment initiation."""
    payment_id: str
    order_id: str
    amount: float
    currency: str
    status: str
    
    class Config:
        from_attributes = True


class PaymentUrlRequest(BaseModel):
    """Request to generate PayHere payment URL."""
    payment_id: str


class PaymentUrlResponse(BaseModel):
    """PayHere payment URL and parameters."""
    payment_url: str
    params: dict


# Helper Functions

def generate_payhere_hash(
    merchant_id: str,
    order_id: str,
    amount: Decimal,
    currency: str,
    merchant_secret: str
) -> str:
    """
    Generate MD5 hash for PayHere.
    
    Format: MERCHANT_ID + ORDER_ID + AMOUNT + CURRENCY + MD5(MERCHANT_SECRET)
    
    Args:
        merchant_id: PayHere merchant ID
        order_id: Order ID
        amount: Payment amount
        currency: Currency code (LKR)
        merchant_secret: PayHere merchant secret
        
    Returns:
        MD5 hash string in uppercase
    """
    # Step 1: Hash the merchant secret
    merchant_secret_hash = hashlib.md5(merchant_secret.encode()).hexdigest().upper()
    
    # Step 2: Build the hash string
    # Format amount to 2 decimal places
    amount_str = f"{float(amount):.2f}"
    hash_string = f"{merchant_id}{order_id}{amount_str}{currency}{merchant_secret_hash}"
    
    # Step 3: Hash the final string
    return hashlib.md5(hash_string.encode()).hexdigest().upper()


def generate_idempotency_key() -> str:
    """Generate a unique idempotency key for payment."""
    return f"pay_{secrets.token_urlsafe(16)}"


# API Endpoints

@router.post("/initiate", response_model=PaymentInitiateResponse, status_code=status.HTTP_201_CREATED)
async def initiate_payment(
    request: PaymentInitiateRequest,
    db: Session = Depends(get_db)
):
    """
    CD-202: Initiate a payment for an order.
    
    This endpoint:
    1. Validates the order exists
    2. Checks for existing pending payments (idempotency)
    3. Creates a new payment record with PENDING status
    4. Returns payment details to the frontend
    
    Args:
        request: Payment initiation request with order_id
        db: Database session
        
    Returns:
        Payment details including payment_id
        
    Raises:
        404: Order not found
        400: Payment already pending for this order
    """
    
    # Get the order
    order = db.query(Order).filter(Order.id == request.order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {request.order_id} not found"
        )
    
    # Check if order already has a pending payment (idempotency check)
    existing_payment = db.query(Payment).filter(
        Payment.order_id == request.order_id,
        Payment.status == PaymentStatus.PENDING
    ).first()
    
    if existing_payment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment already pending for order {request.order_id}"
        )
    
    # Generate unique idempotency key
    idempotency_key = generate_idempotency_key()
    
    # Create payment record
    payment = Payment(
        order_id=order.id,
        user_id=order.user_id,  # From the order
        idempotency_key=idempotency_key,
        amount=order.total_amount,  # Total amount from order
        currency="LKR",
        status=PaymentStatus.PENDING,
        payhere_payment_id=None,  # Will be filled when webhook arrives
        completed_at=None
    )
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    return PaymentInitiateResponse(
        payment_id=str(payment.id),
        order_id=str(order.id),
        amount=float(payment.amount),
        currency=payment.currency,
        status=payment.status.value
    )


@router.post("/generate-url", response_model=PaymentUrlResponse)
async def generate_payment_url(
    request: PaymentUrlRequest,
    db: Session = Depends(get_db)
):
    """
    CD-203: Generate PayHere payment URL with all required parameters.
    
    This endpoint:
    1. Gets the payment record
    2. Gets the associated order details
    3. Generates the PayHere security hash
    4. Returns PayHere URL and all required parameters
    
    Args:
        request: Request with payment_id
        db: Database session
        
    Returns:
        PayHere payment URL and parameters
        
    Raises:
        404: Payment not found
        400: Payment is not in PENDING status
    """
    
    # Get payment record
    payment = db.query(Payment).filter(Payment.id == request.payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment {request.payment_id} not found"
        )
    
    # Verify payment is still pending
    if payment.status != PaymentStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment {request.payment_id} is not pending (status: {payment.status})"
        )
    
    # Get order details
    order = db.query(Order).filter(Order.id == payment.order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {payment.order_id} not found"
        )
    
    # Get PayHere credentials from environment
    merchant_id = os.getenv("PAYHERE_MERCHANT_ID")
    merchant_secret = os.getenv("PAYHERE_MERCHANT_SECRET")
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    
    if not merchant_id or not merchant_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PayHere credentials not configured"
        )
    
    # Generate PayHere hash
    hash_value = generate_payhere_hash(
        merchant_id=merchant_id,
        order_id=str(order.id),
        amount=payment.amount,
        currency=payment.currency,
        merchant_secret=merchant_secret
    )
    
    # Build PayHere parameters
    # These will be sent as form data to PayHere
    payhere_params = {
        "merchant_id": merchant_id,
        "return_url": f"{frontend_url}/payment/success",
        "cancel_url": f"{frontend_url}/payment/cancel",
        "notify_url": f"{backend_url}/api/v1/payments/webhook",
        "order_id": str(order.id),
        "items": f"Vehicle Order - {order.id}",  # Adjust based on your Order model
        "currency": payment.currency,
        "amount": f"{float(payment.amount):.2f}",
        # Customer details from order
        "first_name": order.customer_first_name if hasattr(order, 'customer_first_name') else "Customer",
        "last_name": order.customer_last_name if hasattr(order, 'customer_last_name') else "",
        "email": order.customer_email if hasattr(order, 'customer_email') else "",
        "phone": order.customer_phone if hasattr(order, 'customer_phone') else "",
        "address": order.customer_address if hasattr(order, 'customer_address') else "",
        "city": order.customer_city if hasattr(order, 'customer_city') else "",
        "country": "Sri Lanka",
        "hash": hash_value
    }
    
    # Get PayHere URL from environment
    payhere_url = os.getenv("PAYHERE_SANDBOX_URL", "https://sandbox.payhere.lk/pay/checkout")
    
    return PaymentUrlResponse(
        payment_url=payhere_url,
        params=payhere_params
    )


@router.post("/webhook")
async def payhere_webhook(
    # PayHere sends data as form data
    merchant_id: str,
    order_id: str,
    payment_id: str,
    payhere_amount: str,
    payhere_currency: str,
    status_code: str,
    md5sig: str,
    db: Session = Depends(get_db)
):
    """
    CD-205: PayHere webhook handler.
    
    This endpoint receives notifications from PayHere when payment is completed.
    It verifies the signature and updates the payment status.
    
    IMPORTANT: This will be implemented in a later task, but here's the skeleton.
    
    Args:
        All parameters sent by PayHere
        db: Database session
        
    Returns:
        Success message
    """
    # TODO: Implement webhook verification and payment update
    # This is for CD-205 (payment success/failure handling)
    
    # For now, just return OK so PayHere doesn't retry
    return {"status": "received"}


# Testing Endpoint (Optional - for development only)

@router.get("/test-cards")
async def get_test_cards():
    """
    CD-207: Get PayHere sandbox test card numbers.
    
    This is a helper endpoint for developers to see test card numbers.
    Remove this in production!
    """
    return {
        "sandbox_cards": {
            "successful_payment": {
                "card_number": "4111 1111 1111 1111",
                "expiry": "12/25",
                "cvv": "123",
                "name": "Any Name"
            },
            "failed_payment": {
                "card_number": "4242 4242 4242 4242",
                "expiry": "12/25",
                "cvv": "123",
                "name": "Any Name"
            }
        },
        "note": "Use these cards only in sandbox mode"
    }