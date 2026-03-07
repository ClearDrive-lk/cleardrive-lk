# backend/app/modules/payments/routes.py

"""
Payment API endpoints with PayHere integration.
Author: Tharin
Epic: CD-E5
Stories: CD-40, CD-41, CD-42
"""

from fastapi import APIRouter, Depends, Form, Header, HTTPException, Request, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import hashlib
import json
import secrets
from datetime import datetime
from urllib.parse import urlencode

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.core.redis_client import get_redis
from app.services.payments.idempotency import payment_idempotency
from app.services.payments.payhere_signature import payhere_verifier
from app.services.payment_notifications import (
    send_payment_confirmation_email,
    send_payment_failure_email,
)
from app.core.security import decrypt_field
from app.modules.payments.models import Payment, PaymentStatus
from app.modules.payments.schemas import (
    PaymentInitiate,
    PaymentInitiateResponse,
    PaymentResponse,
)
from app.modules.orders.models import (
    Order,
    OrderStatus,
    OrderStatusHistory,
    PaymentStatus as OrderPaymentStatus,
)
from app.modules.auth.models import User

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

    merchant_secret_hash = hashlib.md5(merchant_secret.encode()).hexdigest().upper()

    hash_string = f"{merchant_id}{order_id}{amount}{currency}{merchant_secret_hash}"

    return hashlib.md5(hash_string.encode()).hexdigest().upper()


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


def _form_value_str(form_data: dict, key: str) -> str | None:
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

    print(f"\n{'='*70}")
    print("PAYMENT INITIATION")
    print(f"{'='*70}")

    idempotency_key = idempotency_key_header or payment_data.idempotency_key
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency key is required (Idempotency-Key header or request body)",
        )
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
    existing_payment = (
        db.query(Payment).filter(Payment.idempotency_key == idempotency_key).first()
    )

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

    # Check if already paid
    existing_completed = (
        db.query(Payment)
        .filter(Payment.order_id == order.id, Payment.status == PaymentStatus.COMPLETED.value)
        .first()
    )

    if existing_completed:
        await redis.delete(lock_key)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order already paid")

    print(f"Order verified: {order.id}")

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

    print(f"Payment created: {payment.id}")

    # ===============================================================
    # STEP 3: GENERATE PAYHERE URL
    # ===============================================================

    response = build_payhere_checkout_response(payment, order, current_user)

    print("PayHere URL generated")
    print(f"{'='*70}\n")

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
async def payhere_webhook(
    merchant_id: str = Form(...),
    order_id: str = Form(...),
    payhere_amount: str = Form(...),
    payhere_currency: str = Form(...),
    status_code: str = Form(...),
    md5sig: str = Form(...),
    payment_id: str | None = Form(default=None),
    method: str | None = Form(default=None),
    status_message: str | None = Form(default=None),
    card_holder_name: str | None = Form(default=None),
    card_no: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    """
    PayHere webhook handler.

    CD-42 flow:
    1. Parse webhook data
    2. Verify MD5 signature
    3. Check idempotency (Redis + DB)
    4. Update payment + order state
    5. Trigger email stubs
    """

    print(f"\n{'='*70}")
    print("PAYHERE WEBHOOK RECEIVED")
    print(f"{'='*70}")

    webhook_data = {
        "merchant_id": merchant_id,
        "order_id": order_id,
        "payment_id": payment_id,
        "payhere_amount": payhere_amount,
        "payhere_currency": payhere_currency,
        "status_code": status_code,
        "md5sig": md5sig,
        "method": method,
        "status_message": status_message,
        "card_holder_name": card_holder_name,
        "card_no": card_no,
    }

    merchant_id = webhook_data["merchant_id"]
    order_id = webhook_data["order_id"]
    payhere_amount = webhook_data["payhere_amount"]
    payhere_currency = webhook_data["payhere_currency"]
    status_code = webhook_data["status_code"]
    provided_signature = webhook_data["md5sig"]
    payhere_payment_id = webhook_data["payment_id"]

    if not merchant_id or not order_id or not payhere_amount or not payhere_currency or not status_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required webhook parameters",
        )

    if not provided_signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signature missing",
        )

    if not payhere_verifier.verify_signature(
        webhook_data=webhook_data,
        provided_signature=provided_signature,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature",
        )

    if payhere_payment_id and await payment_idempotency.is_webhook_processed(payhere_payment_id):
        return {"status": "ok", "message": "Webhook already processed"}

    if payhere_payment_id:
        existing = db.query(Payment).filter(Payment.payhere_payment_id == payhere_payment_id).first()
        if existing:
            return {"status": "ok", "message": "Payment already processed"}

    payment = db.query(Payment).filter(Payment.payhere_order_id == order_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    if payment.status == PaymentStatus.COMPLETED:
        if payhere_payment_id:
            await payment_idempotency.mark_webhook_processed(payhere_payment_id)
        return {"status": "ok", "message": "Payment already successful"}

    order = db.query(Order).filter(Order.id == payment.order_id).first()

    if status_code == "2":
        payment.status = PaymentStatus.COMPLETED
        payment.payhere_payment_id = payhere_payment_id
        payment.payment_method = webhook_data["method"]
        payment.card_holder_name = webhook_data["card_holder_name"]
        card_no = webhook_data["card_no"]
        payment.card_no = card_no[-4:] if card_no else None
        payment.completed_at = datetime.utcnow()

        if order:
            old_status = order.status
            order.status = OrderStatus.PAYMENT_CONFIRMED
            order.payment_status = OrderPaymentStatus.COMPLETED
            history = OrderStatusHistory(
                order_id=order.id,
                from_status=old_status,
                to_status=OrderStatus.PAYMENT_CONFIRMED,
                notes=f"Payment completed: {payhere_payment_id or 'N/A'}",
            )
            db.add(history)
    else:
        payment.status = PaymentStatus.FAILED
        if order:
            order.payment_status = OrderPaymentStatus.FAILED

    try:
        db.commit()
        db.refresh(payment)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database update failed",
        )

    if payhere_payment_id:
        await payment_idempotency.mark_webhook_processed(payhere_payment_id)

    if order:
        try:
            if payment.status == PaymentStatus.COMPLETED:
                await send_payment_confirmation_email(payment, order)
            else:
                await send_payment_failure_email(payment, order)
        except Exception:
            # Webhook should not fail if email service is unavailable.
            pass

    return {
        "status": "ok",
        "payment_id": payhere_payment_id,
        "payment_status": payment.status.value,
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
