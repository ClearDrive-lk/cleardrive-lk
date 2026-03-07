from __future__ import annotations

from decimal import Decimal

from app.core.config import settings
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


def test_initiate_requires_idempotency_header(client, auth_headers, db, test_user, monkeypatch):
    order = _create_order_for_user(db, test_user, stock_no="STOCK-101")
    fake_redis = _FakeRedis()

    async def _get_redis():
        return fake_redis

    monkeypatch.setattr("app.modules.payments.routes.get_redis", _get_redis)

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
    fake_redis = _FakeRedis()

    async def _get_redis():
        return fake_redis

    monkeypatch.setattr("app.modules.payments.routes.get_redis", _get_redis)

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
    fake_redis = _LockedRedis()

    async def _get_redis():
        return fake_redis

    monkeypatch.setattr("app.modules.payments.routes.get_redis", _get_redis)

    headers = {**auth_headers, "Idempotency-Key": "550e8400-e29b-41d4-a716-446655440001"}
    response = client.post(
        "/api/v1/payments/initiate", headers=headers, json={"order_id": str(order.id)}
    )

    assert response.status_code == 409
    assert "already in progress" in response.json()["detail"]


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


def test_payment_model_has_uniqueness_constraints():
    assert Payment.__table__.c.idempotency_key.unique is True
    assert Payment.__table__.c.payhere_payment_id.unique is True
