# backend/app/modules/payments/routes.py

"""
Payment API endpoints with PayHere integration.
Author: Tharin
Epic: CD-E5
Stories: CD-40, CD-41, CD-42
"""

from datetime import datetime
import hashlib
import json
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.core.redis_client import get_redis
from app.modules.auth.models import User
from app.modules.orders.models import Order, OrderStatus, OrderStatusHistory, PaymentStatus as OrderPaymentStatus
from app.modules.payments.models import Payment, PaymentStatus
from app.modules.payments.schemas import (
    PaymentInitiate,
    PaymentInitiateResponse,
    PaymentResponse,
)

router = APIRouter(prefix="/payments", tags=["payments"])


# ===================================================================
# HELPER: GENERATE PAYHERE MD5 SIGNATURE
# ===================================================================

def generate_payhere_hash(
    merchant_id: str,
    order_id: str,
    amount: str,
    currency: str,
    merchant_secret: str
) -> str:
    """
    Generate MD5 hash for PayHere.
    
    Format: MD5(merchant_id + order_id + amount + currency + MD5(merchant_secret))
    """
    
    merchant_secret_hash = hashlib.md5(merchant_secret.encode()).hexdigest().upper()
    
    hash_string = f"{merchant_id}{order_id}{amount}{currency}{merchant_secret_hash}"
    
    return hashlib.md5(hash_string.encode()).hexdigest().upper()


# ===================================================================
# ENDPOINT: INITIATE PAYMENT
# ===================================================================

@router.post("/initiate", response_model=PaymentInitiateResponse)
async def initiate_payment(
    payment_data: PaymentInitiate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initiate PayHere payment.
    
    **Process:**
    1. Check idempotency (prevent duplicate)
    2. Verify order exists and belongs to user
    3. Verify order status is CREATED
    4. Create payment record
    5. Generate PayHere payment URL
    6. Return URL for redirect
    
    **Idempotency:**
    - Client must provide unique idempotency_key
    - If duplicate key, return original response
    - Prevents accidental double charges
    
    **Returns:**
    - PayHere payment URL
    - Redirect user to this URL
    """
    
    print(f"\n{'='*70}")
    print(f"💳 PAYMENT INITIATION")
    print(f"{'='*70}")
    
    # ===============================================================
    # LAYER 1: CHECK IDEMPOTENCY (Redis)
    # ===============================================================
    redis = await get_redis()
    cache_key = f"payment:idempotency:{payment_data.idempotency_key}"
    
    cached_response = await redis.get(cache_key)
    if cached_response:
        print(f"✅ Idempotency hit (Redis): {payment_data.idempotency_key}")
        return json.loads(cached_response)
    
    # ===============================================================
    # LAYER 2: CHECK IDEMPOTENCY (Database)
    # ===============================================================
    existing_payment = db.query(Payment).filter(
        Payment.idempotency_key == payment_data.idempotency_key
    ).first()
    
    if existing_payment:
        print(f"✅ Idempotency hit (Database): {payment_data.idempotency_key}")
        
        response = {
            "payment_id": str(existing_payment.id),
            "payhere_url": f"https://sandbox.payhere.lk/pay/{existing_payment.payhere_order_id}",
            "amount": float(existing_payment.amount),
            "currency": existing_payment.currency,
            "order_id": str(existing_payment.order_id)
        }
        
        # Cache for future requests
        await redis.setex(cache_key, 3600, json.dumps(response, default=str))
        
        return response
    
    # ===============================================================
    # STEP 1: VERIFY ORDER
    # ===============================================================
    order = db.query(Order).filter(Order.id == payment_data.order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {payment_data.order_id} not found"
        )
    
    # Check ownership
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only pay for your own orders"
        )
    
    # Check order status
    if order.status != OrderStatus.CREATED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order status is {order.status}, payment not allowed"
        )
    
    # Check if already paid
    existing_completed = db.query(Payment).filter(
        Payment.order_id == order.id,
        Payment.status == PaymentStatus.COMPLETED
    ).first()
    
    if existing_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order already paid"
        )
    
    print(f"✅ Order verified: {order.id}")
    
    # ===============================================================
    # STEP 2: CREATE PAYMENT RECORD
    # ===============================================================
    payhere_order_id = f"CD-{str(order.id)[:8]}-{int(datetime.utcnow().timestamp())}"
    
    payment = Payment(
        order_id=order.id,
        user_id=current_user.id,
        payhere_order_id=payhere_order_id,
        idempotency_key=payment_data.idempotency_key,
        amount=order.total_cost_lkr,
        currency="LKR",
        status=PaymentStatus.PENDING
    )
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    print(f"💾 Payment created: {payment.id}")
    
    # ===============================================================
    # STEP 3: GENERATE PAYHERE URL
    # ===============================================================
    
    # Generate hash
    hash_value = generate_payhere_hash(
        merchant_id=settings.PAYHERE_MERCHANT_ID,
        order_id=payhere_order_id,
        amount=f"{float(order.total_cost_lkr):.2f}",
        currency="LKR",
        merchant_secret=settings.PAYHERE_MERCHANT_SECRET
    )
    
    # PayHere payment URL (sandbox)
    payhere_base_url = "https://sandbox.payhere.lk/pay/checkout"
    notify_url = settings.PAYHERE_NOTIFY_URL
    return_url = settings.PAYHERE_RETURN_URL.replace("{order_id}", str(order.id))
    cancel_url = settings.PAYHERE_CANCEL_URL.replace("{order_id}", str(order.id))

    payhere_params = {
        "merchant_id": settings.PAYHERE_MERCHANT_ID,
        "order_id": payhere_order_id,
        "items": "Vehicle Import Order",
        "currency": "LKR",
        "amount": f"{float(order.total_cost_lkr):.2f}",
        "first_name": current_user.name or "Customer",
        "last_name": "",
        "email": current_user.email,
        "phone": order.phone,
        "address": order.shipping_address[:50],
        "city": "Colombo",
        "country": "Sri Lanka",
        "hash": hash_value,
        "notify_url": notify_url,
        "return_url": return_url,
        "cancel_url": cancel_url,
    }
    payhere_url = f"{payhere_base_url}?{urlencode(payhere_params)}"
    
    print(f"🔗 PayHere URL generated")
    print(f"{'='*70}\n")
    
    # ===============================================================
    # STEP 4: CACHE RESPONSE
    # ===============================================================
    response = {
        "payment_id": str(payment.id),
        "payhere_url": payhere_url,
        "amount": float(payment.amount),
        "currency": payment.currency,
        "order_id": str(order.id)
    }
    
    # Cache for 1 hour
    await redis.setex(cache_key, 3600, json.dumps(response, default=str))
    
    return response


# ===================================================================
# ENDPOINT: PAYHERE WEBHOOK
# ===================================================================

@router.post("/webhook")
async def payhere_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    PayHere webhook handler.
    
    **Called by PayHere when payment completes.**
    
    **Security:**
    - Verify MD5 signature
    - Check idempotency (prevent duplicate processing)
    - Update order status
    
    **Process:**
    1. Verify signature
    2. Check idempotency
    3. Find payment record
    4. Update payment status
    5. Update order status to PAYMENT_CONFIRMED
    6. Return 200 OK
    """
    
    print(f"\n{'='*70}")
    print(f"📬 PAYHERE WEBHOOK RECEIVED")
    print(f"{'='*70}")
    
    # Get form data
    form_data = await request.form()
    
    merchant_id = form_data.get("merchant_id")
    order_id = form_data.get("order_id")
    payhere_amount = form_data.get("payhere_amount")
    payhere_currency = form_data.get("payhere_currency")
    status_code = form_data.get("status_code")
    md5sig = form_data.get("md5sig")
    payment_id = form_data.get("payment_id")
    method = form_data.get("method")
    card_holder_name = form_data.get("card_holder_name")
    card_no = form_data.get("card_no")
    
    print(f"Order ID: {order_id}")
    print(f"Amount: {payhere_currency} {payhere_amount}")
    print(f"Status: {status_code}")
    print(f"Payment ID: {payment_id}")

    required = [merchant_id, order_id, payhere_amount, payhere_currency, status_code, md5sig]
    if any(v is None for v in required):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required webhook fields",
        )
    
    # ===============================================================
    # STEP 1: VERIFY SIGNATURE
    # ===============================================================
    expected_hash = generate_payhere_hash(
        merchant_id=merchant_id,
        order_id=order_id,
        amount=payhere_amount,
        currency=payhere_currency,
        merchant_secret=settings.PAYHERE_MERCHANT_SECRET
    )
    
    if md5sig.upper() != expected_hash:
        print(f"❌ Invalid signature!")
        print(f"   Expected: {expected_hash}")
        print(f"   Received: {md5sig}")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )
    
    print(f"✅ Signature verified")
    
    # ===============================================================
    # STEP 2: CHECK IDEMPOTENCY (PayHere payment_id)
    # ===============================================================
    if payment_id:
        existing = db.query(Payment).filter(
            Payment.payhere_payment_id == payment_id
        ).first()
        
        if existing:
            print(f"✅ Webhook already processed (payment_id: {payment_id})")
            return {"status": "success", "message": "Already processed"}
    
    # ===============================================================
    # STEP 3: FIND PAYMENT RECORD
    # ===============================================================
    payment = db.query(Payment).filter(
        Payment.payhere_order_id == order_id
    ).first()
    
    if not payment:
        print(f"❌ Payment not found for order: {order_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # ===============================================================
    # STEP 4: UPDATE PAYMENT STATUS
    # ===============================================================
    
    # Status code 2 = Success
    if status_code == "2":
        payment.status = PaymentStatus.COMPLETED
        payment.payhere_payment_id = payment_id
        payment.payment_method = method
        payment.card_holder_name = card_holder_name
        payment.card_no = card_no[-4:] if card_no else None  # Last 4 digits only
        payment.completed_at = datetime.utcnow()
        
        # Update order status
        order = db.query(Order).filter(Order.id == payment.order_id).first()
        
        if order:
            old_status = order.status
            order.status = OrderStatus.PAYMENT_CONFIRMED
            order.payment_status = OrderPaymentStatus.COMPLETED
            
            # Create status history
            history = OrderStatusHistory(
                order_id=order.id,
                from_status=old_status,
                to_status=OrderStatus.PAYMENT_CONFIRMED,
                notes=f"Payment completed: {payment_id}"
            )
            db.add(history)
        
        print(f"✅ Payment successful!")
    
    else:
        payment.status = PaymentStatus.FAILED
        print(f"❌ Payment failed (status: {status_code})")
    
    db.commit()
    
    print(f"{'='*70}\n")
    
    # TODO: Send email notification
    
    return {"status": "success"}


# ===================================================================
# ENDPOINT: GET PAYMENT STATUS
# ===================================================================

@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get payment details."""
    
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment {payment_id} not found"
        )
    
    # Check ownership
    if current_user.role != "ADMIN" and payment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own payments"
        )
    
    return payment
