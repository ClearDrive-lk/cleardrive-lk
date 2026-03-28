from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock

from app.core.config import settings
from app.modules.kyc.models import KYCDocument, KYCStatus
from app.modules.orders.models import Order, OrderStatus
from app.modules.orders.models import PaymentStatus as OrderPaymentStatus
from app.modules.payments.models import Payment, PaymentStatus
from app.modules.payments.routes import generate_payhere_webhook_signature
from app.modules.vehicles.models import Vehicle, VehicleStatus


class _FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def get(self, key: str):
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None, nx: bool = False):
        if nx and key in self.store:
            return False
        self.store[key] = value
        return True

    async def setex(self, key: str, _ttl: int, value: str):
        self.store[key] = value
        return True

    async def delete(self, *keys: str):
        deleted = 0
        for key in keys:
            if key in self.store:
                del self.store[key]
                deleted += 1
        return deleted


class _LockedRedis(_FakeRedis):
    async def set(self, key: str, value: str, ex: int | None = None, nx: bool = False):
        return False


def _create_kyc_for_user(db, test_user, status: KYCStatus) -> KYCDocument:
    kyc = KYCDocument(
        user_id=test_user.id,
        nic_front_url="https://example.com/nic-front.jpg",
        nic_back_url="https://example.com/nic-back.jpg",
        selfie_url="https://example.com/selfie.jpg",
        status=status,
    )
    db.add(kyc)
    db.commit()
    db.refresh(kyc)
    return kyc


def _create_order_for_user(db, test_user, stock_no: str = "STOCK-001") -> Order:
    vehicle = Vehicle(
        stock_no=stock_no,
        make="Toyota",
        model="Prius",
        year=2020,
        price_jpy=Decimal("1500000.00"),
        status=VehicleStatus.AVAILABLE,
    )
    db.add(vehicle)
    db.flush()

    order = Order(
        user_id=test_user.id,
        vehicle_id=vehicle.id,
        status=OrderStatus.CREATED,
        payment_status=OrderPaymentStatus.PENDING,
        shipping_address="123 Main Street, Colombo",
        phone="0771234567",
        total_cost_lkr=Decimal("500000.00"),
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def _mark_payment_otp_verified(fake_redis: _FakeRedis, test_user, order: Order) -> None:
    fake_redis.store[f"payment_otp_verified:{test_user.id}:{order.id}"] = "1"


def test_initiate_requires_idempotency_header(client, auth_headers, db, test_user, monkeypatch):
    order = _create_order_for_user(db, test_user, stock_no="STOCK-101")
    _create_kyc_for_user(db, test_user, KYCStatus.APPROVED)
    fake_redis = _FakeRedis()

    async def _get_redis():
        return fake_redis

    monkeypatch.setattr("app.modules.payments.routes.get_redis", _get_redis)
    _mark_payment_otp_verified(fake_redis, test_user, order)

    response = client.post(
        "/api/v1/payments/initiate",
        headers=auth_headers,
        json={"order_id": str(order.id), "idempotency_key": "1234567890abcdef"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Idempotency-Key header is required"


def test_initiate_returns_cached_response_for_same_key(
    client, auth_headers, db, test_user, monkeypatch
):
    order = _create_order_for_user(db, test_user, stock_no="STOCK-102")
    _create_kyc_for_user(db, test_user, KYCStatus.APPROVED)
    fake_redis = _FakeRedis()

    async def _get_redis():
        return fake_redis

    monkeypatch.setattr("app.modules.payments.routes.get_redis", _get_redis)
    _mark_payment_otp_verified(fake_redis, test_user, order)

    idem_key = "550e8400-e29b-41d4-a716-446655440000"
    headers = {**auth_headers, "Idempotency-Key": idem_key}

    first = client.post(
        "/api/v1/payments/initiate", headers=headers, json={"order_id": str(order.id)}
    )
    second = client.post(
        "/api/v1/payments/initiate", headers=headers, json={"order_id": str(order.id)}
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert db.query(Payment).filter(Payment.order_id == order.id).count() == 1


def test_initiate_returns_409_when_lock_not_acquired(
    client, auth_headers, db, test_user, monkeypatch
):
    order = _create_order_for_user(db, test_user, stock_no="STOCK-103")
    _create_kyc_for_user(db, test_user, KYCStatus.APPROVED)
    fake_redis = _LockedRedis()

    async def _get_redis():
        return fake_redis

    monkeypatch.setattr("app.modules.payments.routes.get_redis", _get_redis)
    _mark_payment_otp_verified(fake_redis, test_user, order)

    headers = {**auth_headers, "Idempotency-Key": "550e8400-e29b-41d4-a716-446655440001"}
    response = client.post(
        "/api/v1/payments/initiate", headers=headers, json={"order_id": str(order.id)}
    )

    assert response.status_code == 409
    assert "already in progress" in response.json()["detail"]


def test_initiate_rejects_amount_above_payhere_limit(
    client, auth_headers, db, test_user, monkeypatch
):
    order = _create_order_for_user(db, test_user, stock_no="STOCK-103A")
    _create_kyc_for_user(db, test_user, KYCStatus.APPROVED)
    order.total_cost_lkr = Decimal("17201470.00")
    db.commit()
    fake_redis = _FakeRedis()

    async def _get_redis():
        return fake_redis

    monkeypatch.setattr("app.modules.payments.routes.get_redis", _get_redis)
    monkeypatch.setattr(
        "app.modules.payments.routes.settings.PAYHERE_MAX_PAYMENT_AMOUNT_LKR",
        Decimal("10000000.00"),
    )
    _mark_payment_otp_verified(fake_redis, test_user, order)

    headers = {**auth_headers, "Idempotency-Key": "550e8400-e29b-41d4-a716-446655440002"}
    response = client.post(
        "/api/v1/payments/initiate", headers=headers, json={"order_id": str(order.id)}
    )

    assert response.status_code == 400
    assert "configured PayHere merchant limit" in response.json()["detail"]
    assert "17,201,470.00" in response.json()["detail"]
    assert db.query(Payment).filter(Payment.order_id == order.id).count() == 0


def test_initiate_requires_existing_kyc(client, auth_headers, db, test_user, monkeypatch):
    order = _create_order_for_user(db, test_user, stock_no="STOCK-103B")
    fake_redis = _FakeRedis()

    async def _get_redis():
        return fake_redis

    monkeypatch.setattr("app.modules.payments.routes.get_redis", _get_redis)
    _mark_payment_otp_verified(fake_redis, test_user, order)

    headers = {**auth_headers, "Idempotency-Key": "550e8400-e29b-41d4-a716-44665544000A"}
    response = client.post(
        "/api/v1/payments/initiate", headers=headers, json={"order_id": str(order.id)}
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "KYC verification required. Please submit your documents first."
    )


def test_initiate_requires_approved_kyc(client, auth_headers, db, test_user, monkeypatch):
    order = _create_order_for_user(db, test_user, stock_no="STOCK-103C")
    _create_kyc_for_user(db, test_user, KYCStatus.PENDING)
    fake_redis = _FakeRedis()

    async def _get_redis():
        return fake_redis

    monkeypatch.setattr("app.modules.payments.routes.get_redis", _get_redis)
    _mark_payment_otp_verified(fake_redis, test_user, order)

    headers = {**auth_headers, "Idempotency-Key": "550e8400-e29b-41d4-a716-44665544000B"}
    response = client.post(
        "/api/v1/payments/initiate", headers=headers, json={"order_id": str(order.id)}
    )

    assert response.status_code == 400
    assert "Only APPROVED users can initiate payment." in response.json()["detail"]


def test_initiate_requires_verified_payment_otp(client, auth_headers, db, test_user, monkeypatch):
    order = _create_order_for_user(db, test_user, stock_no="STOCK-103D")
    _create_kyc_for_user(db, test_user, KYCStatus.APPROVED)
    fake_redis = _FakeRedis()

    async def _get_redis():
        return fake_redis

    monkeypatch.setattr("app.modules.payments.routes.get_redis", _get_redis)

    headers = {**auth_headers, "Idempotency-Key": "550e8400-e29b-41d4-a716-44665544000C"}
    response = client.post(
        "/api/v1/payments/initiate", headers=headers, json={"order_id": str(order.id)}
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"] == "Payment OTP verification required before initiating payment."
    )


def test_request_and_verify_payment_otp(client, auth_headers, db, test_user, monkeypatch):
    order = _create_order_for_user(db, test_user, stock_no="STOCK-103E")
    _create_kyc_for_user(db, test_user, KYCStatus.APPROVED)
    fake_redis = _FakeRedis()
    sent_otps: list[str] = []

    async def _get_redis():
        return fake_redis

    async def _send_otp_email(_email: str, otp: str, _name: str | None = None) -> bool:
        sent_otps.append(otp)
        return True

    monkeypatch.setattr("app.modules.payments.routes.get_redis", _get_redis)
    monkeypatch.setattr("app.modules.payments.routes.send_otp_email", _send_otp_email)

    request_response = client.post(
        "/api/v1/payments/request-otp",
        headers=auth_headers,
        json={"order_id": str(order.id)},
    )

    assert request_response.status_code == 200
    assert request_response.json()["message"] == "Payment OTP sent to your email."
    assert len(sent_otps) == 1

    verify_response = client.post(
        "/api/v1/payments/verify-otp",
        headers=auth_headers,
        json={"order_id": str(order.id), "otp": sent_otps[0]},
    )

    assert verify_response.status_code == 200
    assert verify_response.json()["verified"] is True
    assert fake_redis.store.get(f"payment_otp_verified:{test_user.id}:{order.id}") == "1"


def test_webhook_dedup_returns_already_processed(client, db, test_user):
    order = _create_order_for_user(db, test_user, stock_no="STOCK-104")
    existing = Payment(
        order_id=order.id,
        user_id=test_user.id,
        payhere_payment_id="PH-DEDUP-001",
        payhere_order_id="CD-ORDER-DEDUP",
        idempotency_key="550e8400-e29b-41d4-a716-446655440099",
        amount=Decimal("500000.00"),
        currency="LKR",
        status=PaymentStatus.PENDING,
    )
    db.add(existing)
    db.commit()

    merchant_id = settings.PAYHERE_MERCHANT_ID
    order_id = "CD-ORDER-DEDUP"
    payhere_amount = "500000.00"
    payhere_currency = "LKR"
    status_code = "2"
    md5sig = generate_payhere_webhook_signature(
        merchant_id=merchant_id,
        order_id=order_id,
        payhere_amount=payhere_amount,
        payhere_currency=payhere_currency,
        status_code=status_code,
        merchant_secret=settings.PAYHERE_MERCHANT_SECRET,
    )

    response = client.post(
        "/api/v1/payments/webhook",
        data={
            "merchant_id": merchant_id,
            "order_id": order_id,
            "payment_id": "PH-DEDUP-001",
            "payhere_amount": payhere_amount,
            "payhere_currency": payhere_currency,
            "status_code": status_code,
            "md5sig": md5sig,
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Already processed"


def test_webhook_rejects_invalid_signature(client, db, test_user):
    order = _create_order_for_user(db, test_user, stock_no="STOCK-105")
    payment = Payment(
        order_id=order.id,
        user_id=test_user.id,
        payhere_order_id="CD-ORDER-BAD-SIG",
        idempotency_key="550e8400-e29b-41d4-a716-446655440100",
        amount=Decimal("500000.00"),
        currency="LKR",
        status=PaymentStatus.PENDING,
    )
    db.add(payment)
    db.commit()

    response = client.post(
        "/api/v1/payments/webhook",
        data={
            "merchant_id": settings.PAYHERE_MERCHANT_ID,
            "order_id": "CD-ORDER-BAD-SIG",
            "payment_id": "PH-BAD-SIG-001",
            "payhere_amount": "500000.00",
            "payhere_currency": "LKR",
            "status_code": "2",
            "md5sig": "INVALID_SIGNATURE",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid signature"


def test_webhook_success_updates_payment_order_and_sends_email(client, db, test_user, monkeypatch):
    order = _create_order_for_user(db, test_user, stock_no="STOCK-106")
    payment = Payment(
        order_id=order.id,
        user_id=test_user.id,
        payhere_order_id="CD-ORDER-SUCCESS",
        idempotency_key="550e8400-e29b-41d4-a716-446655440101",
        amount=Decimal("500000.00"),
        currency="LKR",
        status=PaymentStatus.PENDING,
    )
    db.add(payment)
    db.commit()

    mock_success_email = AsyncMock()
    mock_failure_email = AsyncMock()
    monkeypatch.setattr(
        "app.modules.payments.routes.send_payment_confirmation_email",
        mock_success_email,
    )
    monkeypatch.setattr(
        "app.modules.payments.routes.send_payment_failure_email",
        mock_failure_email,
    )

    md5sig = generate_payhere_webhook_signature(
        merchant_id=settings.PAYHERE_MERCHANT_ID,
        order_id="CD-ORDER-SUCCESS",
        payhere_amount="500000.00",
        payhere_currency="LKR",
        status_code="2",
        merchant_secret=settings.PAYHERE_MERCHANT_SECRET,
    )

    response = client.post(
        "/api/v1/payments/webhook",
        data={
            "merchant_id": settings.PAYHERE_MERCHANT_ID,
            "order_id": "CD-ORDER-SUCCESS",
            "payment_id": "PH-SUCCESS-001",
            "payhere_amount": "500000.00",
            "payhere_currency": "LKR",
            "status_code": "2",
            "status_message": "Authorized",
            "method": "VISA",
            "card_holder_name": "Test User",
            "card_no": "************1234",
            "md5sig": md5sig,
        },
    )

    db.refresh(payment)
    db.refresh(order)

    assert response.status_code == 200
    assert response.json()["payment_status"] == "COMPLETED"
    assert payment.status == PaymentStatus.COMPLETED
    assert payment.payhere_payment_id == "PH-SUCCESS-001"
    assert payment.payment_method == "VISA"
    assert payment.card_holder_name == "Test User"
    assert payment.card_no == "1234"
    assert order.status == OrderStatus.PAYMENT_CONFIRMED
    assert order.payment_status == OrderPaymentStatus.COMPLETED
    mock_success_email.assert_awaited_once()
    mock_failure_email.assert_not_awaited()


def test_webhook_failure_marks_payment_failed_and_sends_failure_email(
    client, db, test_user, monkeypatch
):
    order = _create_order_for_user(db, test_user, stock_no="STOCK-107")
    payment = Payment(
        order_id=order.id,
        user_id=test_user.id,
        payhere_order_id="CD-ORDER-FAILED",
        idempotency_key="550e8400-e29b-41d4-a716-446655440102",
        amount=Decimal("500000.00"),
        currency="LKR",
        status=PaymentStatus.PENDING,
    )
    db.add(payment)
    db.commit()

    mock_success_email = AsyncMock()
    mock_failure_email = AsyncMock()
    monkeypatch.setattr(
        "app.modules.payments.routes.send_payment_confirmation_email",
        mock_success_email,
    )
    monkeypatch.setattr(
        "app.modules.payments.routes.send_payment_failure_email",
        mock_failure_email,
    )

    md5sig = generate_payhere_webhook_signature(
        merchant_id=settings.PAYHERE_MERCHANT_ID,
        order_id="CD-ORDER-FAILED",
        payhere_amount="500000.00",
        payhere_currency="LKR",
        status_code="-2",
        merchant_secret=settings.PAYHERE_MERCHANT_SECRET,
    )

    response = client.post(
        "/api/v1/payments/webhook",
        data={
            "merchant_id": settings.PAYHERE_MERCHANT_ID,
            "order_id": "CD-ORDER-FAILED",
            "payment_id": "PH-FAILED-001",
            "payhere_amount": "500000.00",
            "payhere_currency": "LKR",
            "status_code": "-2",
            "status_message": "Insufficient funds",
            "md5sig": md5sig,
        },
    )

    db.refresh(payment)
    db.refresh(order)

    assert response.status_code == 200
    assert response.json()["payment_status"] == "FAILED"
    assert payment.status == PaymentStatus.FAILED
    assert order.status == OrderStatus.CREATED
    assert order.payment_status == OrderPaymentStatus.FAILED
    mock_success_email.assert_not_awaited()
    mock_failure_email.assert_awaited_once()


def test_payment_model_has_uniqueness_constraints():
    assert Payment.__table__.c.idempotency_key.unique is True
    assert Payment.__table__.c.payhere_payment_id.unique is True
