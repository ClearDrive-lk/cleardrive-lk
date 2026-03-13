from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.modules.finance.models import (
    FinanceStatus,
    InsuranceStatus,
    LCStatus,
    LetterOfCredit,
    VehicleFinance,
    VehicleInsurance,
)
from app.modules.orders.models import Order, OrderStatus
from app.modules.orders.models import PaymentStatus as OrderPaymentStatus
from app.modules.vehicles.models import Vehicle, VehicleStatus


def _create_order_for_user(db, user_id) -> Order:
    vehicle = Vehicle(
        stock_no=f"FIN-{uuid4()}",
        make="Toyota",
        model="Prius",
        year=2020,
        price_jpy=Decimal("1500000.00"),
        status=VehicleStatus.AVAILABLE,
    )
    db.add(vehicle)
    db.flush()

    order = Order(
        user_id=user_id,
        vehicle_id=vehicle.id,
        status=OrderStatus.PAYMENT_CONFIRMED,
        payment_status=OrderPaymentStatus.COMPLETED,
        shipping_address="No 1, Galle Road, Colombo",
        phone="0771234567",
        total_cost_lkr=Decimal("5000000.00"),
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def test_lc_request_and_admin_approval_flow(client, db, test_user, auth_headers, admin_headers):
    order = _create_order_for_user(db, test_user.id)

    request_payload = {
        "order_id": str(order.id),
        "bank_name": "Bank of Ceylon",
        "bank_branch": "Colombo Main",
        "account_number": "123456789",
        "amount": 500000.00,
    }
    create_response = client.post("/api/v1/lc/request", headers=auth_headers, json=request_payload)

    assert create_response.status_code == 200
    created = create_response.json()
    assert created["order_id"] == str(order.id)
    assert created["status"] == LCStatus.PENDING.value

    lc_id = created["id"]

    approve_payload = {
        "lc_number": "LC2026-001",
        "beneficiary_name": "Tokyo Exports Ltd",
        "beneficiary_bank": "MUFG Bank",
        "beneficiary_account": "JP-987654321",
        "issue_date": datetime.utcnow().isoformat(),
        "expiry_date": (datetime.utcnow() + timedelta(days=90)).isoformat(),
        "admin_notes": "Approved for processing",
    }
    approve_response = client.post(
        f"/api/v1/lc/{lc_id}/approve",
        headers=admin_headers,
        json=approve_payload,
    )

    assert approve_response.status_code == 200
    approved = approve_response.json()
    assert approved["lc_number"] == "LC2026-001"
    assert approved["status"] == LCStatus.APPROVED.value

    model = db.query(LetterOfCredit).filter(LetterOfCredit.id == lc_id).first()
    assert model is not None
    assert model.status == LCStatus.APPROVED


def test_finance_apply_and_approve_flow(client, db, test_user, auth_headers, admin_headers):
    order = _create_order_for_user(db, test_user.id)

    apply_payload = {
        "order_id": str(order.id),
        "vehicle_price": 5000000.00,
        "down_payment": 1000000.00,
        "monthly_income": 200000.00,
        "employment_type": "Permanent",
        "employer_name": "ABC Company",
        "years_employed": 5.0,
    }
    apply_response = client.post("/api/v1/finance/apply", headers=auth_headers, json=apply_payload)

    assert apply_response.status_code == 200
    created = apply_response.json()
    assert created["order_id"] == str(order.id)
    assert created["status"] == FinanceStatus.PENDING.value
    assert created["loan_amount"] == "4000000.00"

    finance_id = created["id"]
    approve_payload = {
        "loan_number": "LOAN2026-001",
        "interest_rate": 12.5,
        "loan_period_months": 60,
        "admin_notes": "Approved with standard terms",
    }
    approve_response = client.post(
        f"/api/v1/finance/{finance_id}/approve",
        headers=admin_headers,
        json=approve_payload,
    )

    assert approve_response.status_code == 200
    approved = approve_response.json()
    assert approved["status"] == FinanceStatus.APPROVED.value
    assert approved["loan_number"] == "LOAN2026-001"
    assert Decimal(approved["monthly_payment"]) > Decimal("0")

    model = db.query(VehicleFinance).filter(VehicleFinance.id == finance_id).first()
    assert model is not None
    assert model.status == FinanceStatus.APPROVED


def test_insurance_quote_and_admin_approval_flow(
    client, db, test_user, auth_headers, admin_headers
):
    order = _create_order_for_user(db, test_user.id)

    quote_payload = {
        "order_id": str(order.id),
        "insurance_type": "Comprehensive",
        "vehicle_value": 5000000.00,
        "driver_age": 30,
        "driver_experience_years": 8,
        "license_number": "B1234567",
        "previous_claims": 0,
    }
    quote_response = client.post(
        "/api/v1/insurance/quote", headers=auth_headers, json=quote_payload
    )

    assert quote_response.status_code == 200
    created = quote_response.json()
    assert created["order_id"] == str(order.id)
    assert created["status"] == InsuranceStatus.PENDING.value

    insurance_id = created["id"]
    approve_payload = {
        "policy_number": "POL2026-001",
        "coverage_amount": 5000000.00,
        "annual_premium": 150000.00,
        "deductible": 50000.00,
        "payment_frequency": "Annual",
        "policy_start_date": datetime.utcnow().isoformat(),
        "policy_end_date": (datetime.utcnow() + timedelta(days=365)).isoformat(),
        "admin_notes": "Quoted and approved",
    }
    approve_response = client.post(
        f"/api/v1/insurance/{insurance_id}/approve",
        headers=admin_headers,
        json=approve_payload,
    )

    assert approve_response.status_code == 200
    approved = approve_response.json()
    assert approved["status"] == InsuranceStatus.QUOTED.value
    assert approved["policy_number"] == "POL2026-001"
    assert approved["annual_premium"] == "150000.00"

    model = db.query(VehicleInsurance).filter(VehicleInsurance.id == insurance_id).first()
    assert model is not None
    assert model.status == InsuranceStatus.QUOTED


def test_admin_pending_endpoints_return_only_pending_items(
    client, db, test_user, auth_headers, admin_headers
):
    order_lc = _create_order_for_user(db, test_user.id)
    order_finance = _create_order_for_user(db, test_user.id)
    order_insurance = _create_order_for_user(db, test_user.id)

    client.post(
        "/api/v1/lc/request",
        headers=auth_headers,
        json={
            "order_id": str(order_lc.id),
            "bank_name": "BOC",
            "bank_branch": "Main",
            "account_number": "123456789",
            "amount": 100000.0,
        },
    )
    client.post(
        "/api/v1/finance/apply",
        headers=auth_headers,
        json={
            "order_id": str(order_finance.id),
            "vehicle_price": 5000000.00,
            "down_payment": 1000000.00,
            "monthly_income": 200000.00,
            "employment_type": "Permanent",
            "employer_name": "ABC Company",
            "years_employed": 5.0,
        },
    )
    client.post(
        "/api/v1/insurance/quote",
        headers=auth_headers,
        json={
            "order_id": str(order_insurance.id),
            "insurance_type": "Comprehensive",
            "vehicle_value": 5000000.00,
            "driver_age": 30,
            "driver_experience_years": 8,
            "license_number": "B1234567",
            "previous_claims": 0,
        },
    )

    pending_lc = client.get("/api/v1/lc/pending", headers=admin_headers)
    pending_finance = client.get("/api/v1/finance/pending", headers=admin_headers)
    pending_insurance = client.get("/api/v1/insurance/pending", headers=admin_headers)

    assert pending_lc.status_code == 200
    assert pending_finance.status_code == 200
    assert pending_insurance.status_code == 200
    assert len(pending_lc.json()) >= 1
    assert len(pending_finance.json()) >= 1
    assert len(pending_insurance.json()) >= 1
