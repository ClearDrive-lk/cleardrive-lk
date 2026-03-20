"""Tests for CD-22 tax calculator service and endpoint."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from app.models.gazette import (
    ApplyOn,
    CustomsRule,
    Gazette,
    GazetteStatus,
    LuxuryTaxRule,
    SurchargeRule,
    TaxFuelType,
    TaxRule,
    TaxVehicleType,
    VehicleTaxRule,
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


def test_calculate_specific_excise_per_kw_with_age_and_power(db):
    gazette = Gazette(
        gazette_no="TEST/ELECTRIC/PERKW",
        effective_date=date(2025, 2, 1),
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
        category_code="PASSENGER_VEHICLE_BEV",
        engine_min=0,
        engine_max=999999,
        power_kw_min=Decimal("50.01"),
        power_kw_max=Decimal("100.00"),
        age_years_min=Decimal("0"),
        age_years_max=Decimal("3"),
        customs_percent=0.0,
        excise_percent=0.0,
        excise_per_kw_amount=Decimal("24100"),
        vat_percent=15.0,
        pal_percent=0.0,
        cess_percent=0.0,
        apply_on=ApplyOn.CIF.value,
        effective_date=date(2025, 2, 1),
        is_active=True,
    )
    db.add(rule)
    db.commit()

    calculator = TaxCalculator(db)
    result = calculator.calculate_import_duty(
        "ELECTRIC",
        "ELECTRIC",
        0,
        8_000_000.0,
        power_kw=75,
        vehicle_age_years=2,
        category_codes=["PASSENGER_VEHICLE_BEV"],
    )

    assert result["excise_duty"] == 1_807_500.0
    assert result["rule_used"]["excise_per_kw_amount"] == 24100.0
    assert result["rule_used"]["category_code"] == "PASSENGER_VEHICLE_BEV"


def test_calculate_tax_with_surcharge_and_luxury_tax(db):
    gazette = Gazette(
        gazette_no="TEST/ELECTRIC/FULL-STACK",
        effective_date=date(2025, 2, 1),
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
        category_code="PASSENGER_VEHICLE_BEV",
        hs_code="8703.80.33",
        engine_min=0,
        engine_max=999999,
        power_kw_min=Decimal("100.01"),
        power_kw_max=Decimal("200.00"),
        age_years_min=Decimal("1.01"),
        age_years_max=Decimal("3.00"),
        customs_percent=Decimal("20.0"),
        surcharge_percent=Decimal("50.0"),
        excise_percent=Decimal("0.0"),
        excise_per_kw_amount=Decimal("60400"),
        vat_percent=Decimal("15.0"),
        pal_percent=Decimal("0.0"),
        cess_percent=Decimal("0.0"),
        luxury_tax_threshold=Decimal("5000000"),
        luxury_tax_percent=Decimal("10.0"),
        apply_on=ApplyOn.CIF.value,
        effective_date=date(2025, 2, 1),
        is_active=True,
    )
    db.add(rule)
    db.commit()

    calculator = TaxCalculator(db)
    result = calculator.calculate_import_duty(
        "ELECTRIC",
        "ELECTRIC",
        0,
        8_000_000.0,
        power_kw=120,
        vehicle_age_years=2,
        category_codes=["PASSENGER_VEHICLE_BEV"],
    )

    assert result["customs_duty"] == 1_600_000.0
    assert result["surcharge"] == 800_000.0
    assert result["excise_duty"] == 7_248_000.0
    assert result["vat"] == 2_647_200.0
    assert result["luxury_tax"] == 800_000.0
    assert result["total_duty"] == 13_095_200.0
    assert result["rule_used"]["hs_code"] == "8703.80.33"
    assert result["rule_used"]["surcharge_percent"] == 50.0


def test_calculate_tax_uses_dedicated_rule_tables(db):
    gazette = Gazette(
        gazette_no="TEST/DEDICATED/2025",
        effective_date=date(2025, 2, 1),
        raw_extracted={},
        status=GazetteStatus.APPROVED.value,
    )
    db.add(gazette)
    db.commit()
    db.refresh(gazette)

    db.add(
        VehicleTaxRule(
            gazette_id=gazette.id,
            category_code="PASSENGER_VEHICLE_BEV",
            fuel_type=TaxFuelType.ELECTRIC.value,
            hs_code="8703.80.33",
            power_kw_min=Decimal("100.01"),
            power_kw_max=Decimal("200.00"),
            age_years_min=Decimal("1.01"),
            age_years_max=Decimal("3.00"),
            excise_type="PER_KW",
            excise_rate=Decimal("60400"),
            effective_date=date(2025, 2, 1),
            is_active=True,
        )
    )
    db.add(
        CustomsRule(
            gazette_id=gazette.id,
            hs_code="8703.80.33",
            customs_percent=Decimal("20"),
            vat_percent=Decimal("15"),
            pal_percent=Decimal("10"),
            cess_type="FIXED",
            cess_value=Decimal("250000"),
            effective_date=date(2025, 2, 1),
            is_active=True,
        )
    )
    db.add(
        SurchargeRule(
            gazette_id=gazette.id,
            name="CUSTOMS_SURCHARGE",
            rate_percent=Decimal("50"),
            applies_to="CUSTOMS_DUTY",
            effective_date=date(2025, 2, 1),
            is_active=True,
        )
    )
    db.add(
        LuxuryTaxRule(
            gazette_id=gazette.id,
            hs_code="8703.80.33",
            threshold_value=Decimal("5000000"),
            rate_percent=Decimal("10"),
            effective_date=date(2025, 2, 1),
            is_active=True,
        )
    )
    db.commit()

    calculator = TaxCalculator(db)
    result = calculator.calculate_import_duty(
        "ELECTRIC",
        "ELECTRIC",
        0,
        8_000_000.0,
        power_kw=120,
        vehicle_age_years=2,
        category_codes=["PASSENGER_VEHICLE_BEV"],
    )

    assert result["customs_duty"] == 1_600_000.0
    assert result["surcharge"] == 800_000.0
    assert result["excise_duty"] == 7_248_000.0
    assert result["pal"] == 800_000.0
    assert result["cess"] == 250_000.0
    assert result["vat"] == 2_804_700.0
    assert result["luxury_tax"] == 300_000.0
    assert result["total_duty"] == 13_802_700.0
    assert result["rule_used"]["rule_source"] == "DEDICATED_RULE_TABLES"
    assert result["rule_used"]["cess_type"] == "FIXED"
