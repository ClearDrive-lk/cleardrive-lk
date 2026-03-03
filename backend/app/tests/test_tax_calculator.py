"""Tests for CD-22 tax calculator service and endpoint."""

from __future__ import annotations

from datetime import date

import pytest
from app.models.gazette import (
    ApplyOn,
    Gazette,
    GazetteStatus,
    TaxFuelType,
    TaxRule,
    TaxVehicleType,
)
from app.services.tax_calculator import NoTaxRuleError, TaxCalculator


@pytest.fixture
def sample_tax_rule(db):
    gazette = Gazette(
        gazette_no="TEST/2024/01",
        effective_date=date(2024, 1, 1),
        raw_extracted={},
        status=GazetteStatus.APPROVED.value,
    )
    db.add(gazette)
    db.commit()
    db.refresh(gazette)

    rule = TaxRule(
        gazette_id=gazette.id,
        vehicle_type=TaxVehicleType.SEDAN.value,
        fuel_type=TaxFuelType.PETROL.value,
        engine_min=1000,
        engine_max=1500,
        customs_percent=25.0,
        excise_percent=50.0,
        vat_percent=15.0,
        pal_percent=7.5,
        cess_percent=30.0,
        apply_on=ApplyOn.CIF_PLUS_CUSTOMS.value,
        effective_date=date(2024, 1, 1),
        is_active=True,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def test_calculate_basic(db, sample_tax_rule):
    calculator = TaxCalculator(db)
    result = calculator.calculate_import_duty(
        vehicle_type="SEDAN",
        fuel_type="PETROL",
        engine_cc=1200,
        cif_value=5_000_000.0,
    )
    assert result["cif_value"] == 5_000_000.0
    assert result["customs_duty"] == 1_250_000.0
    assert "rule_used" in result
    assert result["rule_used"]["gazette_no"] == "TEST/2024/01"


def test_no_matching_rule(db):
    calculator = TaxCalculator(db)
    with pytest.raises(NoTaxRuleError):
        calculator.calculate_import_duty("SEDAN", "PETROL", 5000, 5_000_000.0)


def test_apply_on_customs_only(db):
    gazette = Gazette(
        gazette_no="TEST/CUSTOMS_ONLY",
        effective_date=date(2024, 1, 1),
        raw_extracted={},
        status=GazetteStatus.APPROVED.value,
    )
    db.add(gazette)
    db.commit()
    db.refresh(gazette)

    rule = TaxRule(
        gazette_id=gazette.id,
        vehicle_type=TaxVehicleType.ELECTRIC.value,
        fuel_type=TaxFuelType.ELECTRIC.value,
        engine_min=0,
        engine_max=999999,
        customs_percent=0.0,
        excise_percent=10.0,
        vat_percent=15.0,
        pal_percent=7.5,
        cess_percent=0.0,
        apply_on=ApplyOn.CUSTOMS_ONLY.value,
        effective_date=date(2024, 1, 1),
        is_active=True,
    )
    db.add(rule)
    db.commit()

    calculator = TaxCalculator(db)
    result = calculator.calculate_import_duty("ELECTRIC", "ELECTRIC", 0, 8_000_000.0)
    assert result["customs_duty"] == 0.0
    assert result["excise_duty"] == 0.0


def test_invalid_vehicle_type(db):
    calculator = TaxCalculator(db)
    with pytest.raises(ValueError, match="Invalid vehicle_type"):
        calculator.calculate_import_duty("SPACESHIP", "PETROL", 1200, 5_000_000.0)


def test_calculate_tax_endpoint(client, sample_tax_rule):
    response = client.post(
        "/api/v1/calculate/tax",
        json={
            "vehicle_type": "SEDAN",
            "fuel_type": "PETROL",
            "engine_cc": 1200,
            "cif_value": 5_000_000,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_duty" in data
    assert "rule_used" in data


def test_no_rule_found_404(client):
    response = client.post(
        "/api/v1/calculate/tax",
        json={
            "vehicle_type": "SEDAN",
            "fuel_type": "PETROL",
            "engine_cc": 9999,
            "cif_value": 5_000_000,
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "NO_TAX_RULE_FOUND"


def test_invalid_parameters_400(client):
    response = client.post(
        "/api/v1/calculate/tax",
        json={
            "vehicle_type": "INVALID",
            "fuel_type": "PETROL",
            "engine_cc": 1200,
            "cif_value": 5_000_000,
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "INVALID_PARAMETERS"
