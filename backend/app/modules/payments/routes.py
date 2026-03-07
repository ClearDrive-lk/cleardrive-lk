# backend/app/modules/payments/routes.py

"""
Payment API endpoints with PayHere integration.
Author: Tharin
Epic: CD-E5
Stories: CD-40, CD-41, CD-42
"""

import hashlib
import json
import secrets
from datetime import datetime
from typing import Any, Mapping
from urllib.parse import urlencode

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.redis_client import get_redis
from app.core.security import decrypt_field
from app.modules.auth.models import User
from app.modules.orders.models import (
    Order,
    OrderStatus,
    OrderStatusHistory,
)
from app.modules.orders.models import PaymentStatus as OrderPaymentStatus
from app.modules.payments.models import Payment, PaymentStatus
from app.modules.payments.schemas import (
    PaymentInitiate,
    PaymentInitiateResponse,
    PaymentResponse,
)
from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

router = APIRouter(prefix="/payments", tags=["payments"])


# ===================================================================
# HELPER: GENERATE PAYHERE MD5 SIGNATURE
# ===================================================================


def generate_payhere_hash(
    merchant_id: str, order_id: str, amount: str, currency: str, merchant_secret: str
) -> str:
    """
    Generate MD5 hash for PayHere.

    Format: MD5(merchant_id + order_id + amount + currency + MD5(merchant_secret))
    """

    merchant_secret_hash = (
        hashlib.md5(merchant_secret.encode(), usedforsecurity=False).hexdigest().upper()
    )

    hash_string = f"{merchant_id}{order_id}{amount}{currency}{merchant_secret_hash}"

    return hashlib.md5(hash_string.encode(), usedforsecurity=False).hexdigest().upper()


def generate_payhere_webhook_signature(
    merchant_id: str,
    order_id: str,
    payhere_amount: str,
    payhere_currency: str,
    status_code: str,
    merchant_secret: str,
) -> str:
    """Generate webhook md5sig using PayHere notification signature format."""
    merchant_secret_hash = (
        hashlib.md5(merchant_secret.encode(), usedforsecurity=False).hexdigest().upper()
    )
    hash_string = f"{merchant_id}{order_id}{payhere_amount}{payhere_currency}{status_code}{merchant_secret_hash}"
    return hashlib.md5(hash_string.encode(), usedforsecurity=False).hexdigest().upper()


def build_payhere_checkout_response(payment: Payment, order: Order, current_user: User) -> dict:
    """Build POST checkout payload and debug URL."""
    if not payment.payhere_order_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Missing PayHere order ID on payment record",
        )
    amount = f"{float(payment.amount):.2f}"
    hash_value = generate_payhere_hash(
        merchant_id=settings.PAYHERE_MERCHANT_ID,
        order_id=payment.payhere_order_id,
        amount=amount,
        currency=payment.currency,
        merchant_secret=settings.PAYHERE_MERCHANT_SECRET,
    )

    decrypted_address = decrypt_field(order.shipping_address) or order.shipping_address
    customer_address = (decrypted_address or "No.1, Galle Road").strip()[:100]

    payment_url = (
        "https://sandbox.payhere.lk/pay/checkout"
        if settings.PAYHERE_SANDBOX
        else "https://www.payhere.lk/pay/checkout"
    )
    payhere_params = {
        "merchant_id": settings.PAYHERE_MERCHANT_ID,
        "return_url": settings.PAYHERE_RETURN_URL.format(order_id=order.id),
        "cancel_url": settings.PAYHERE_CANCEL_URL.format(order_id=order.id),
        "notify_url": settings.PAYHERE_NOTIFY_URL,
        "first_name": current_user.name or "Customer",
        "last_name": "",
        "email": current_user.email,
        "phone": order.phone,
        "address": customer_address,
        "city": "Colombo",
        "country": "Sri Lanka",
        "order_id": payment.payhere_order_id,
        "items": "Vehicle Import Order",
        "currency": payment.currency,
        "amount": amount,
        "hash": hash_value,
    }

    return {
        "payment_id": str(payment.id),
        "payment_url": payment_url,
        "payhere_params": payhere_params,
        "payhere_url": f"{payment_url}?{urlencode(payhere_params)}",
        "amount": float(payment.amount),
        "currency": payment.currency,
        "order_id": str(order.id),
    }


def _form_value_str(form_data: Mapping[str, Any], key: str) -> str | None:
    """Safely normalize form values to strings."""
    value = form_data.get(key)
    if value is None or isinstance(value, UploadFile):
        return None
    return str(value)


# ===================================================================
# ENDPOINT: INITIATE PAYMENT
# ===================================================================


@router.post("/initiate", response_model=PaymentInitiateResponse)
async def initiate_payment(
    payment_data: PaymentInitiate,
    idempotency_key_header: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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

    print(f"\n{'=' * 70}")
    print("ðŸ’³ PAYMENT INITIATION")
    print(f"{'=' * 70}")

    if not idempotency_key_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required",
        )
    idempotency_key = idempotency_key_header
    if len(idempotency_key) < 16:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency key must be at least 16 characters",
        )

    # ===============================================================
    # LAYER 1: CHECK IDEMPOTENCY (Redis)
    # ===============================================================
    redis = await get_redis()
    cache_key = f"payment:idempotency:{idempotency_key}"
    lock_key = f"{cache_key}:lock"

    cached_response = await redis.get(cache_key)
    if cached_response:
        print(f"Idempotency hit (Redis): {idempotency_key}")
        return json.loads(cached_response)

    lock_acquired = await redis.set(lock_key, "1", ex=30, nx=True)
    if not lock_acquired:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment request is already in progress for this idempotency key",
        )

    # ===============================================================
    # LAYER 2: CHECK IDEMPOTENCY (Database)
    # ===============================================================
    existing_payment = db.query(Payment).filter(Payment.idempotency_key == idempotency_key).first()

    if existing_payment:
        print(f"Idempotency hit (Database): {idempotency_key}")

        order = db.query(Order).filter(Order.id == existing_payment.order_id).first()
        if not order:
            await redis.delete(lock_key)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {existing_payment.order_id} not found",
            )
        response = build_payhere_checkout_response(existing_payment, order, current_user)

        # Cache for future requests
        await redis.setex(cache_key, 3600, json.dumps(response, default=str))

        await redis.delete(lock_key)
        return response

    # ===============================================================
    # STEP 1: VERIFY ORDER
    # ===============================================================
    order = db.query(Order).filter(Order.id == payment_data.order_id).first()

    if not order:
        await redis.delete(lock_key)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Order {payment_data.order_id} not found"
        )

    # Check ownership
    if order.user_id != current_user.id:
        await redis.delete(lock_key)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You can only pay for your own orders"
        )

    # Check order status
    if order.status != OrderStatus.CREATED:
        await redis.delete(lock_key)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order status is {order.status}, payment not allowed",
        )

    # Layered duplicate prevention by order:
    # if a payment already exists for this order, reuse it instead of creating a new row.
    existing_order_payment = (
        db.query(Payment)
        .filter(Payment.order_id == order.id)
        .order_by(Payment.created_at.desc())
        .first()
    )
    if existing_order_payment:
        if existing_order_payment.status == PaymentStatus.COMPLETED:
            await redis.delete(lock_key)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Order already paid"
            )
        if existing_order_payment.status in {PaymentStatus.PENDING, PaymentStatus.PROCESSING}:
            response = build_payhere_checkout_response(existing_order_payment, order, current_user)
            await redis.setex(cache_key, 3600, json.dumps(response, default=str))
            await redis.delete(lock_key)
            return response

    print(f"âœ… Order verified: {order.id}")

    # ===============================================================
    # STEP 2: CREATE PAYMENT RECORD
    # ===============================================================
    payhere_order_id = (
        f"CD-{str(order.id)[:8]}-{int(datetime.utcnow().timestamp())}-{secrets.token_hex(3)}"
    )

    payment = Payment(
        order_id=order.id,
        user_id=current_user.id,
        payhere_order_id=payhere_order_id,
        idempotency_key=idempotency_key,
        amount=order.total_cost_lkr,
        currency="LKR",
        status=PaymentStatus.PENDING.value,
    )

    db.add(payment)
    try:
        db.commit()
        db.refresh(payment)
    except IntegrityError:
        db.rollback()
        existing_payment = (
            db.query(Payment).filter(Payment.idempotency_key == idempotency_key).first()
        )
        if not existing_payment:
            await redis.delete(lock_key)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Duplicate payment request detected",
            )
        response = build_payhere_checkout_response(existing_payment, order, current_user)
        await redis.setex(cache_key, 3600, json.dumps(response, default=str))
        await redis.delete(lock_key)
        return response

    print(f"ðŸ’¾ Payment created: {payment.id}")

    # ===============================================================
    # STEP 3: GENERATE PAYHERE URL
    # ===============================================================

    response = build_payhere_checkout_response(payment, order, current_user)

    print("ðŸ”— PayHere URL generated")
    print(f"{'=' * 70}\n")

    # ===============================================================
    # STEP 4: CACHE RESPONSE
    # ===============================================================
    # Cache for 1 hour
    await redis.setex(cache_key, 3600, json.dumps(response, default=str))

    await redis.delete(lock_key)
    return response


# ===================================================================
# ENDPOINT: PAYHERE WEBHOOK
# ===================================================================


@router.post("/webhook")
async def payhere_webhook(request: Request, db: Session = Depends(get_db)):
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

    print(f"\n{'=' * 70}")
    print("ðŸ“¬ PAYHERE WEBHOOK RECEIVED")
    print(f"{'=' * 70}")

    # Get form data
    form_data = await request.form()

    merchant_id = _form_value_str(form_data, "merchant_id")
    order_id = _form_value_str(form_data, "order_id")
    payhere_amount = _form_value_str(form_data, "payhere_amount")
    payhere_currency = _form_value_str(form_data, "payhere_currency")
    status_code = _form_value_str(form_data, "status_code")
    md5sig = _form_value_str(form_data, "md5sig")
    payment_id = _form_value_str(form_data, "payment_id")
    method = _form_value_str(form_data, "method")
    card_holder_name = _form_value_str(form_data, "card_holder_name")
    card_no = _form_value_str(form_data, "card_no")

    if (
        not merchant_id
        or not order_id
        or not payhere_amount
        or not payhere_currency
        or not status_code
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required webhook parameters",
        )

    print(f"Order ID: {order_id}")
    print(f"Amount: {payhere_currency} {payhere_amount}")
    print(f"Status: {status_code}")
    print(f"Payment ID: {payment_id}")

    # ===============================================================
    # STEP 1: VERIFY SIGNATURE
    # ===============================================================
    expected_hash = generate_payhere_webhook_signature(
        merchant_id=merchant_id,
        order_id=order_id,
        payhere_amount=payhere_amount,
        payhere_currency=payhere_currency,
        status_code=status_code,
        merchant_secret=settings.PAYHERE_MERCHANT_SECRET,
    )

    if not md5sig or md5sig.upper() != expected_hash:
        print("âŒ Invalid signature!")
        print(f"   Expected: {expected_hash}")
        print(f"   Received: {md5sig}")

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    print("âœ… Signature verified")
    # ===============================================================
    # STEP 2: CHECK IDEMPOTENCY (PayHere payment_id)
    # ===============================================================
    if payment_id:
        existing = db.query(Payment).filter(Payment.payhere_payment_id == payment_id).first()

        if existing:
            print(f"âœ… Webhook already processed (payment_id: {payment_id})")
            return {"status": "success", "message": "Already processed"}

    # ===============================================================
    # STEP 3: FIND PAYMENT RECORD
    # ===============================================================
    payment = db.query(Payment).filter(Payment.payhere_order_id == order_id).first()

    if not payment:
        print(f"âŒ Payment not found for order: {order_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

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
                notes=f"Payment completed: {payment_id}",
            )
            db.add(history)

        print("âœ… Payment successful!")
    else:
        payment.status = PaymentStatus.FAILED
        print(f"âŒ Payment failed (status: {status_code})")

    db.commit()

    print(f"{'=' * 70}\n")

    # TODO: Send email notification

    return {"status": "success"}


@router.get("/test-cards")
async def get_test_cards():
    """PayHere sandbox cards for QA/testing only."""
    return {
        "sandbox_cards": {
            "visa_success": {"card_number": "4916217792925942", "cvv": "123"},
            "mastercard_success": {"card_number": "5307167694146682", "cvv": "123"},
            "visa_failed": {"card_number": "4007702601644397", "cvv": "123"},
        },
        "note": "Use only in PayHere sandbox mode.",
    }


# ===================================================================
# ENDPOINT: GET PAYMENT STATUS
# ===================================================================


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get payment details."""

    payment = db.query(Payment).filter(Payment.id == payment_id).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Payment {payment_id} not found"
        )

    # Check ownership
    if current_user.role != "ADMIN" and payment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You can only view your own payments"
        )

    return payment
