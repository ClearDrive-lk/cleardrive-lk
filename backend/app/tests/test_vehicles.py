# backend/app/tests/test_vehicles.py

"""
Test vehicle endpoints.
Author: Parindra Chameekara
Epic: CD-E3 - Vehicle Management System
"""

import os
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
from app.models.tax_rule_catalog import GlobalTaxParameter, HSCodeMatrixRule
from app.modules.vehicles.cost_calculator import calculate_platform_fee
from app.modules.vehicles.models import (
    Drive,
    FuelType,
    Steering,
    Transmission,
    Vehicle,
    VehicleStatus,
    VehicleType,
)
from app.services.scraper.auction_scraper import AuctionSiteScraper
from app.services.scraper.scheduler import ScraperScheduler, _normalize_row_enums


@pytest.fixture(autouse=True)
def _mock_live_exchange_rate(monkeypatch):
    monkeypatch.setattr(
        "app.modules.vehicles.routes._get_live_exchange_rate_payload",
        lambda base, symbols: {
            "base": base.upper(),
            "target": symbols.upper(),
            "rate": 2.0808,
            "date": "2025-10-01",
            "provider": "cbsl_sell_rate",
            "source": "Central Bank of Sri Lanka Exchange Rates (Sell Rate)",
            "rate_type": "sell",
            "fetched_at": "2026-03-20T00:00:00",
        },
    )


def _seed_default_tax_rule(db):
    """Seed one active tax rule used by /vehicles/{id}/cost tests."""
    gazette = Gazette(
        gazette_no="TEST/VEHICLES/COST",
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
        fuel_type=TaxFuelType.HYBRID.value,
        engine_min=0,
        engine_max=5000,
        customs_percent=25.0,
        excise_percent=35.0,
        vat_percent=15.0,
        pal_percent=7.5,
        cess_percent=5.0,
        apply_on=ApplyOn.CIF_PLUS_CUSTOMS.value,
        effective_date=date(2024, 1, 1),
        is_active=True,
    )
    db.add(rule)
    db.commit()


def test_get_vehicles_empty(client, db):
    """Test getting vehicles when none exist."""
    response = client.get("/api/v1/vehicles")

    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 0
    assert data["vehicles"] == []
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["limit"] == 20
    assert data["pagination"]["total_pages"] == 0


def test_get_vehicles_with_data(client, db):
    """Test getting vehicles when data exists."""

    # Create test vehicle
    vehicle = Vehicle(
        stock_no="TEST-001",
        make="Toyota",
        model="Prius",
        year=2020,
        price_jpy=1850000,
        mileage_km=35000,
        engine_cc=1800,
        fuel_type=FuelType.HYBRID,
        transmission=Transmission.AUTOMATIC,
        status=VehicleStatus.AVAILABLE,
    )
    db.add(vehicle)
    db.commit()

    # Get vehicles
    response = client.get("/api/v1/vehicles")

    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 1
    assert len(data["vehicles"]) == 1
    assert data["vehicles"][0]["make"] == "Toyota"
    assert data["vehicles"][0]["model"] == "Prius"
    assert data["vehicles"][0]["year"] == 2020
    assert data["vehicles"][0]["stock_no"] == "TEST-001"


def test_zero_price_vehicle_gets_display_price_fallback(client, db):
    """List response should provide a display price for zero-priced rows."""

    priced_reference = Vehicle(
        stock_no="HZ-REF-1",
        make="Honda",
        model="Vezel",
        year=2026,
        price_jpy=3200000,
        status=VehicleStatus.AVAILABLE,
    )
    missing_price = Vehicle(
        stock_no="HZ-ZERO-1",
        make="Honda",
        model="Vezel",
        year=2026,
        price_jpy=0,
        status=VehicleStatus.AVAILABLE,
    )
    db.add(priced_reference)
    db.add(missing_price)
    db.commit()

    response = client.get("/api/v1/vehicles", params={"search": "HZ-ZERO-1"})

    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 1
    assert float(data["vehicles"][0]["price_jpy"]) == 3200000

    # Ensure DB remains unchanged; fallback is response-only.
    db.refresh(missing_price)
    assert float(missing_price.price_jpy) == 0.0


def test_search_vehicles_by_make(client, db):
    """Test vehicle search by make."""

    # Create test vehicles
    vehicles = [
        Vehicle(stock_no="T1", make="Toyota", model="Prius", year=2020, price_jpy=1850000),
        Vehicle(stock_no="T2", make="Toyota", model="Aqua", year=2019, price_jpy=1250000),
        Vehicle(stock_no="H1", make="Honda", model="Fit", year=2020, price_jpy=1350000),
    ]

    for v in vehicles:
        db.add(v)
    db.commit()

    # Search for Toyota
    response = client.get("/api/v1/vehicles", params={"search": "Toyota"})

    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 2
    # Search for Honda
    response = client.get("/api/v1/vehicles", params={"search": "Honda"})

    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 1


def test_search_vehicles_by_stock_or_chassis(client, db):
    """Search should match stock and chassis identifiers used in the catalog UI."""

    vehicle = Vehicle(
        stock_no="CAT-SEARCH-01",
        chassis="CHS-987654",
        make="Toyota",
        model="Prius",
        year=2020,
        price_jpy=1850000,
    )
    db.add(vehicle)
    db.commit()

    stock_response = client.get("/api/v1/vehicles", params={"search": "CAT-SEARCH-01"})
    assert stock_response.status_code == 200
    assert stock_response.json()["pagination"]["total"] == 1

    chassis_response = client.get("/api/v1/vehicles", params={"search": "CHS-987654"})
    assert chassis_response.status_code == 200
    assert chassis_response.json()["pagination"]["total"] == 1


def test_filter_vehicles_by_make(client, db):
    """Test filtering vehicles by make."""

    # Create test vehicles
    vehicles = [
        Vehicle(stock_no="T1", make="Toyota", model="Prius", year=2020, price_jpy=1850000),
        Vehicle(stock_no="T2", make="Toyota", model="Aqua", year=2019, price_jpy=1250000),
        Vehicle(stock_no="H1", make="Honda", model="Fit", year=2020, price_jpy=1350000),
    ]

    for v in vehicles:
        db.add(v)
    db.commit()

    # Filter by Toyota
    response = client.get("/api/v1/vehicles", params={"make": "Toyota"})

    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 2
    for vehicle in data["vehicles"]:
        assert "Toyota" in vehicle["make"]


def test_filter_vehicles_by_year_range(client, db):
    """Test filtering vehicles by year range."""

    # Create test vehicles
    vehicles = [
        Vehicle(stock_no="V1", make="Toyota", model="Prius", year=2018, price_jpy=1500000),
        Vehicle(stock_no="V2", make="Honda", model="Fit", year=2020, price_jpy=1350000),
        Vehicle(stock_no="V3", make="Mazda", model="CX-5", year=2022, price_jpy=2500000),
    ]

    for v in vehicles:
        db.add(v)
    db.commit()

    # Filter 2019-2021
    response = client.get("/api/v1/vehicles", params={"year_min": 2019, "year_max": 2021})

    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 1
    assert data["vehicles"][0]["year"] == 2020


def test_recent_only_defaults_to_last_3_years_when_enabled(client, db):
    """Test recent_only filter applies 3-year window when year_min is omitted."""
    current_year = date.today().year
    vehicles = [
        Vehicle(
            stock_no="R1",
            make="Toyota",
            model="Prius",
            year=current_year - 1,
            price_jpy=1800000,
        ),
        Vehicle(
            stock_no="R2",
            make="Toyota",
            model="Corolla",
            year=current_year - 6,
            price_jpy=1400000,
        ),
    ]
    for v in vehicles:
        db.add(v)
    db.commit()

    response = client.get("/api/v1/vehicles", params={"recent_only": "true"})

    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 1
    assert data["vehicles"][0]["stock_no"] == "R1"


def test_filter_vehicles_by_price_range(client, db):
    """Test filtering vehicles by price range."""

    # Create test vehicles
    vehicles = [
        Vehicle(stock_no="V1", make="Toyota", model="Prius", year=2020, price_jpy=1000000),
        Vehicle(stock_no="V2", make="Honda", model="Fit", year=2020, price_jpy=1500000),
        Vehicle(stock_no="V3", make="Mazda", model="CX-5", year=2020, price_jpy=2500000),
    ]

    for v in vehicles:
        db.add(v)
    db.commit()

    # Filter 1000000-2000000
    response = client.get("/api/v1/vehicles", params={"price_min": 1000000, "price_max": 2000000})

    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 2


def test_filter_vehicles_by_fuel_type(client, db):
    """Test filtering vehicles by fuel type."""

    # Create test vehicles
    vehicles = [
        Vehicle(
            stock_no="V1",
            make="Toyota",
            model="Prius",
            year=2020,
            price_jpy=1850000,
            fuel_type=FuelType.HYBRID,
        ),
        Vehicle(
            stock_no="V2",
            make="Honda",
            model="Fit",
            year=2020,
            price_jpy=1350000,
            fuel_type=FuelType.GASOLINE,
        ),
        Vehicle(
            stock_no="V3",
            make="Tesla",
            model="Model 3",
            year=2021,
            price_jpy=4500000,
            fuel_type=FuelType.ELECTRIC,
        ),
    ]

    for v in vehicles:
        db.add(v)
    db.commit()

    # Filter by Hybrid
    response = client.get("/api/v1/vehicles", params={"fuel_type": "Gasoline/hybrid"})

    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 1
    assert data["vehicles"][0]["fuel_type"] == "Gasoline/hybrid"


def test_filter_hybrid_includes_plugin_hybrid_variants(client, db):
    """Hybrid-focused filters should include plugin-hybrid scraped variants."""

    vehicles = [
        Vehicle(
            stock_no="HY-1",
            make="Toyota",
            model="Prius",
            year=2020,
            price_jpy=1850000,
            fuel_type=FuelType.HYBRID,
        ),
        Vehicle(
            stock_no="HY-2",
            make="Mitsubishi",
            model="Outlander",
            year=2021,
            price_jpy=3200000,
            fuel_type=FuelType.PLUGIN_HYBRID,
        ),
        Vehicle(
            stock_no="HY-3",
            make="Honda",
            model="Fit",
            year=2020,
            price_jpy=1350000,
            fuel_type=FuelType.GASOLINE,
        ),
    ]
    for vehicle in vehicles:
        db.add(vehicle)
    db.commit()

    response = client.get("/api/v1/vehicles", params={"fuel_type": "Hybrid"})

    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 2
    returned_fuels = {item["fuel_type"] for item in data["vehicles"]}
    assert "Gasoline/hybrid" in returned_fuels
    assert "Plugin Hybrid" in returned_fuels


def test_filter_vehicle_type_uses_body_type_aliases(client, db):
    """Type filters should still work when scraper kept only body_type text."""

    vehicles = [
        Vehicle(
            stock_no="VT-1",
            make="Mazda",
            model="CX-5",
            year=2020,
            price_jpy=2400000,
            body_type="SUVs",
        ),
        Vehicle(
            stock_no="VT-2",
            make="Toyota",
            model="Land Cruiser",
            year=2021,
            price_jpy=5200000,
            vehicle_type=VehicleType.SUV,
        ),
        Vehicle(
            stock_no="VT-3",
            make="Toyota",
            model="Corolla",
            year=2019,
            price_jpy=1800000,
            vehicle_type=VehicleType.SEDAN,
        ),
    ]
    for vehicle in vehicles:
        db.add(vehicle)
    db.commit()

    response = client.get("/api/v1/vehicles", params={"vehicle_type": "SUV"})

    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 2
    stock_nos = {item["stock_no"] for item in data["vehicles"]}
    assert {"VT-1", "VT-2"}.issubset(stock_nos)


def test_vehicle_catalog_quick_filter_values(client, db):
    """Mirror the exact quick-filter values used by the web catalog."""

    vehicles = [
        Vehicle(
            stock_no="QF-TOYOTA",
            make="Toyota",
            model="Harrier",
            year=2021,
            price_jpy=4200000,
            vehicle_type=VehicleType.SUV,
            body_type="SUV",
            fuel_type=FuelType.HYBRID,
            transmission=Transmission.AUTOMATIC,
        ),
        Vehicle(
            stock_no="QF-HONDA",
            make="Honda",
            model="Fit",
            year=2020,
            price_jpy=3200000,
            vehicle_type=VehicleType.HATCHBACK,
            body_type="Hatchback",
            fuel_type=FuelType.GASOLINE,
            transmission=Transmission.AUTOMATIC,
        ),
        Vehicle(
            stock_no="QF-ELECTRIC",
            make="Nissan",
            model="Leaf",
            year=2022,
            price_jpy=6100000,
            vehicle_type=VehicleType.SUV,
            body_type="SUV",
            fuel_type=FuelType.ELECTRIC,
            transmission=Transmission.AUTOMATIC,
        ),
        Vehicle(
            stock_no="QF-LUXURY",
            make="Lexus",
            model="LX600",
            year=2023,
            price_jpy=16800000,
            vehicle_type=VehicleType.SUV,
            body_type="SUV",
            fuel_type=FuelType.GASOLINE,
            transmission=Transmission.AUTOMATIC,
        ),
    ]
    for vehicle in vehicles:
        db.add(vehicle)
    db.commit()

    response = client.get("/api/v1/vehicles", params={"search": "Toyota"})
    assert response.status_code == 200
    assert response.json()["pagination"]["total"] == 1

    response = client.get("/api/v1/vehicles", params={"search": "Honda"})
    assert response.status_code == 200
    assert response.json()["pagination"]["total"] == 1

    response = client.get("/api/v1/vehicles", params={"price_max": 5000000})
    assert response.status_code == 200
    assert response.json()["pagination"]["total"] == 2

    response = client.get("/api/v1/vehicles", params={"fuel_type": "Gasoline/Hybrid"})
    assert response.status_code == 200
    assert response.json()["pagination"]["total"] == 1

    response = client.get("/api/v1/vehicles", params={"vehicle_type": "SUVs", "search": "QF-"})
    assert response.status_code == 200
    assert response.json()["pagination"]["total"] == 3

    response = client.get("/api/v1/vehicles", params={"fuel_type": "Electric"})
    assert response.status_code == 200
    assert response.json()["pagination"]["total"] == 1

    response = client.get("/api/v1/vehicles", params={"price_min": 15000000})
    assert response.status_code == 200
    assert response.json()["pagination"]["total"] == 1


def test_pagination(client, db):
    """Test pagination functionality."""

    # Create 25 test vehicles
    vehicles = [
        Vehicle(stock_no=f"V{i}", make="Toyota", model="Prius", year=2020, price_jpy=1000000 + i)
        for i in range(25)
    ]

    for v in vehicles:
        db.add(v)
    db.commit()

    # Get page 1 with limit 10
    response = client.get("/api/v1/vehicles", params={"page": 1, "limit": 10})

    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 25
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["limit"] == 10
    assert data["pagination"]["total_pages"] == 3
    assert len(data["vehicles"]) == 10

    # Get page 2
    response = client.get("/api/v1/vehicles", params={"page": 2, "limit": 10})

    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["page"] == 2
    assert len(data["vehicles"]) == 10


def test_sorting_by_price(client, db):
    """Test sorting vehicles by price."""

    # Create test vehicles
    vehicles = [
        Vehicle(stock_no="V1", make="Toyota", model="Prius", year=2020, price_jpy=2000000),
        Vehicle(stock_no="V2", make="Honda", model="Fit", year=2020, price_jpy=1000000),
        Vehicle(stock_no="V3", make="Mazda", model="CX-5", year=2020, price_jpy=1500000),
    ]

    for v in vehicles:
        db.add(v)
    db.commit()

    # Sort ascending
    response = client.get("/api/v1/vehicles", params={"sort_by": "price_jpy", "sort_order": "asc"})

    assert response.status_code == 200
    data = response.json()
    assert float(data["vehicles"][0]["price_jpy"]) == 1000000
    assert float(data["vehicles"][1]["price_jpy"]) == 1500000
    assert float(data["vehicles"][2]["price_jpy"]) == 2000000

    # Sort descending
    response = client.get("/api/v1/vehicles", params={"sort_by": "price_jpy", "sort_order": "desc"})

    assert response.status_code == 200
    data = response.json()
    assert float(data["vehicles"][0]["price_jpy"]) == 2000000
    assert float(data["vehicles"][1]["price_jpy"]) == 1500000
    assert float(data["vehicles"][2]["price_jpy"]) == 1000000


def test_list_makes(client, db):
    """Test getting list of all makes."""

    # Create test vehicles
    vehicles = [
        Vehicle(stock_no="V1", make="Toyota", model="Prius", year=2020, price_jpy=1850000),
        Vehicle(stock_no="V2", make="Honda", model="Fit", year=2020, price_jpy=1350000),
        Vehicle(stock_no="V3", make="Mazda", model="CX-5", year=2020, price_jpy=2500000),
        Vehicle(stock_no="V4", make="Toyota", model="Aqua", year=2019, price_jpy=1250000),
    ]

    for v in vehicles:
        db.add(v)
    db.commit()

    # Get makes list
    response = client.get("/api/v1/vehicles/makes/list")

    assert response.status_code == 200
    data = response.json()
    assert "makes" in data
    assert len(data["makes"]) == 3
    assert "Toyota" in data["makes"]
    assert "Honda" in data["makes"]
    assert "Mazda" in data["makes"]


def test_list_models(client, db):
    """Test getting list of all models."""

    # Create test vehicles
    vehicles = [
        Vehicle(stock_no="V1", make="Toyota", model="Prius", year=2020, price_jpy=1850000),
        Vehicle(stock_no="V2", make="Toyota", model="Aqua", year=2019, price_jpy=1250000),
        Vehicle(stock_no="V3", make="Honda", model="Fit", year=2020, price_jpy=1350000),
    ]

    for v in vehicles:
        db.add(v)
    db.commit()

    # Get all models
    response = client.get("/api/v1/vehicles/models/list")

    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) == 3
    assert "Prius" in data["models"]
    assert "Aqua" in data["models"]
    assert "Fit" in data["models"]


def test_list_models_filtered_by_make(client, db):
    """Test getting list of models filtered by make."""

    # Create test vehicles
    vehicles = [
        Vehicle(stock_no="V1", make="Toyota", model="Prius", year=2020, price_jpy=1850000),
        Vehicle(stock_no="V2", make="Toyota", model="Aqua", year=2019, price_jpy=1250000),
        Vehicle(stock_no="V3", make="Honda", model="Fit", year=2020, price_jpy=1350000),
    ]

    for v in vehicles:
        db.add(v)
    db.commit()

    # Get Toyota models only
    response = client.get("/api/v1/vehicles/models/list", params={"make": "Toyota"})

    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) == 2
    assert "Prius" in data["models"]
    assert "Aqua" in data["models"]
    assert "Fit" not in data["models"]


def test_get_vehicle_by_id(client, db):
    """Test getting a specific vehicle by ID."""

    # Create test vehicle
    vehicle = Vehicle(
        stock_no="TEST-001",
        make="Toyota",
        model="Prius",
        year=2020,
        price_jpy=1850000,
        mileage_km=35000,
        engine_cc=1800,
        fuel_type=FuelType.HYBRID,
        transmission=Transmission.AUTOMATIC,
        steering=Steering.RIGHT_HAND,
        drive=Drive.TWO_WD,
        status=VehicleStatus.AVAILABLE,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    # Get vehicle by ID
    response = client.get(f"/api/v1/vehicles/{vehicle.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["stock_no"] == "TEST-001"
    assert data["make"] == "Toyota"
    assert data["model"] == "Prius"
    assert data["year"] == 2020


def test_get_vehicle_not_found(client, db):
    """Test getting a vehicle that doesn't exist."""

    # Use a random UUID
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = client.get(f"/api/v1/vehicles/{fake_id}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_exchange_rate_uses_cbsl_source(client):
    response = client.get(
        "/api/v1/vehicles/exchange-rate", params={"base": "JPY", "symbols": "LKR"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["base"] == "JPY"
    assert data["target"] == "LKR"
    assert data["rate"] == 2.0808
    assert data["provider"] == "cbsl_sell_rate"
    assert data["source"] == "Central Bank of Sri Lanka Exchange Rates (Sell Rate)"
    assert data["date"] == "2025-10-01"


def test_calculate_cost(client, db):
    """Test calculating cost for a vehicle."""
    _seed_default_tax_rule(db)

    # Create test vehicle
    vehicle = Vehicle(
        stock_no="TEST-001",
        make="Toyota",
        model="Prius",
        year=2020,
        price_jpy=2000000,
        mileage_km=35000,
        engine_cc=1800,
        vehicle_type=VehicleType.SEDAN,
        fuel_type=FuelType.HYBRID,
        transmission=Transmission.AUTOMATIC,
        status=VehicleStatus.AVAILABLE,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    # Calculate cost
    response = client.get(f"/api/v1/vehicles/{vehicle.id}/cost")

    assert response.status_code == 200
    data = response.json()

    # Check all required fields are present
    assert "vehicle_price_jpy" in data
    assert "vehicle_price_lkr" in data
    assert "exchange_rate" in data
    assert "exchange_rate_source" in data
    assert "exchange_rate_date" in data
    assert "shipping_cost_lkr" in data
    assert "customs_duty_lkr" in data
    assert "vat_lkr" in data
    assert "total_cost_lkr" in data
    assert "platform_fee" in data
    assert "platform_fee_lkr" in data
    assert "vehicle_percentage" in data
    assert "taxes_percentage" in data
    assert "fees_percentage" in data

    # Check values are positive
    assert float(data["vehicle_price_jpy"]) == 2000000
    assert data["exchange_rate_source"] == "Central Bank of Sri Lanka Exchange Rates (Sell Rate)"
    assert data["exchange_rate_date"] == "2025-10-01"
    assert float(data["total_cost_lkr"]) > 0
    assert float(data["platform_fee_lkr"]) > 0
    assert data["platform_fee"]["description"] == "ClearDrive Service Fee"


def test_calculate_platform_fee_tiers():
    assert calculate_platform_fee(7_999_999.99) == 120000
    assert calculate_platform_fee(8_000_000) == 180000
    assert calculate_platform_fee(15_000_000) == 180000
    assert calculate_platform_fee(20_000_000) == 180000
    assert calculate_platform_fee(20_000_000.01) == 300000


def test_calculate_cost_applies_mid_platform_fee_at_8m_boundary(client, db):
    _seed_default_tax_rule(db)
    vehicle = Vehicle(
        stock_no="TEST-BOUNDARY-MID",
        make="Toyota",
        model="Prius",
        year=2020,
        price_jpy=1500000,
        engine_cc=1800,
        vehicle_type=VehicleType.SEDAN,
        fuel_type=FuelType.HYBRID,
        status=VehicleStatus.AVAILABLE,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    response = client.get(f"/api/v1/vehicles/{vehicle.id}/cost")
    assert response.status_code == 200
    data = response.json()
    assert data["platform_fee"]["tier"] in {"LOW", "MID", "HIGH"}
    assert float(data["platform_fee"]["amount"]) == float(data["platform_fee_lkr"])


def test_calculate_platform_fee_boundary_values_exact():
    assert calculate_platform_fee(8_000_000.0) == 180000
    assert calculate_platform_fee(20_000_000.0) == 180000


def test_calculate_cost_custom_exchange_rate(client, db):
    """Test calculating cost with custom exchange rate."""
    _seed_default_tax_rule(db)

    # Create test vehicle
    vehicle = Vehicle(
        stock_no="TEST-001",
        make="Toyota",
        model="Prius",
        year=2020,
        price_jpy=1000000,
        engine_cc=1500,
        vehicle_type=VehicleType.SEDAN,
        fuel_type=FuelType.HYBRID,
        status=VehicleStatus.AVAILABLE,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    # Calculate cost with custom exchange rate
    response = client.get(f"/api/v1/vehicles/{vehicle.id}/cost", params={"exchange_rate": 2.0})

    assert response.status_code == 200
    data = response.json()
    assert float(data["exchange_rate"]) == 2.0
    assert float(data["vehicle_price_lkr"]) == 2000000  # 1000000 * 2.0


def test_calculate_cost_requires_approved_tax_rule(client, db):
    vehicle = Vehicle(
        stock_no="TEST-NO-RULE",
        make="Toyota",
        model="Prius",
        year=2020,
        price_jpy=1000000,
        engine_cc=1800,
        vehicle_type=VehicleType.SEDAN,
        fuel_type=FuelType.HYBRID,
        status=VehicleStatus.AVAILABLE,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    response = client.get(f"/api/v1/vehicles/{vehicle.id}/cost")

    assert response.status_code == 404
    detail = response.json()["detail"]
    assert (
        "No approved tax rule matches this vehicle yet" in detail
        or "No approved gazette tax rule matches this vehicle yet" in detail
        or "No HS-code matrix rule matches this vehicle" in detail
    )


def test_calculate_cost_uses_approved_gazette_rules(client, db, admin_headers, admin_user):
    gazette = Gazette(
        gazette_no="2024/APPROVED-COST",
        effective_date=None,
        raw_extracted={
            "effective_date": "2024-02-01",
            "rules": [
                {
                    "vehicle_type": "SEDAN",
                    "fuel_type": "HYBRID",
                    "engine_min": 1500,
                    "engine_max": 2000,
                    "customs_percent": 25,
                    "excise_percent": 35,
                    "vat_percent": 15,
                    "pal_percent": 7.5,
                    "cess_percent": 5,
                    "apply_on": "CIF_PLUS_CUSTOMS",
                }
            ],
        },
        status="PENDING",
        uploaded_by=admin_user.id,
    )
    db.add(gazette)
    db.commit()
    db.refresh(gazette)

    approve_response = client.post(f"/api/v1/gazette/{gazette.id}/approve", headers=admin_headers)
    assert approve_response.status_code == 200

    vehicle = Vehicle(
        stock_no="TEST-GAZETTE-RULE",
        make="Toyota",
        model="Prius",
        year=2020,
        price_jpy=1000000,
        engine_cc=1800,
        vehicle_type=VehicleType.SEDAN,
        fuel_type=FuelType.HYBRID,
        transmission=Transmission.AUTOMATIC,
        status=VehicleStatus.AVAILABLE,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    response = client.get(f"/api/v1/vehicles/{vehicle.id}/cost")

    assert response.status_code == 200
    data = response.json()
    assert float(data["customs_duty_lkr"]) == 565200.0
    assert float(data["pal_lkr"]) > 0


def test_calculate_cost_uses_approved_catalog_rules(client, db, admin_headers, admin_user):
    global_gazette = Gazette(
        gazette_no="CATALOG/GLOBAL/2026",
        effective_date=date(2026, 4, 1),
        raw_extracted={
            "source": "CATALOG_GLOBAL_TAX_PARAMETERS",
            "dataset": "global_tax_parameters",
            "effective_date": "2026-04-01",
            "catalog_rows": [
                {
                    "parameter_group": "CUSTOMS_RULE",
                    "parameter_name": "SURCHARGE_RATE",
                    "condition_or_type": "BRAND_NEW",
                    "value": 50,
                    "unit": "%",
                    "calculation_order": 2,
                    "applicability_flag": "ALL",
                },
                {
                    "parameter_group": "GENERAL_TAX",
                    "parameter_name": "VAT",
                    "condition_or_type": "STANDARD_RATE",
                    "value": 18,
                    "unit": "%",
                    "calculation_order": 8,
                    "applicability_flag": "ALL",
                },
                {
                    "parameter_group": "FIXED_FEES",
                    "parameter_name": "VEL",
                    "condition_or_type": "PER_UNIT",
                    "value": 15000,
                    "unit": "LKR",
                    "calculation_order": 10,
                    "applicability_flag": "ALL",
                },
                {
                    "parameter_group": "FIXED_FEES",
                    "parameter_name": "COM_EXM_SEL",
                    "condition_or_type": "PER_UNIT",
                    "value": 1750,
                    "unit": "LKR",
                    "calculation_order": 11,
                    "applicability_flag": "ALL",
                },
                {
                    "parameter_group": "LUXURY_TAX",
                    "parameter_name": "THRESHOLD_HYBRID_PETROL",
                    "condition_or_type": "HYBRID",
                    "value": 5500000,
                    "unit": "LKR",
                    "calculation_order": 9,
                    "applicability_flag": "PASSENGER_ONLY",
                },
                {
                    "parameter_group": "LUXURY_TAX",
                    "parameter_name": "RATE_HYBRID_PETROL",
                    "condition_or_type": "ON_EXCESS_VALUE",
                    "value": 80,
                    "unit": "%",
                    "calculation_order": 9,
                    "applicability_flag": "PASSENGER_ONLY",
                },
            ],
        },
        status="PENDING",
        uploaded_by=admin_user.id,
    )
    hs_gazette = Gazette(
        gazette_no="CATALOG/HS/2026",
        effective_date=date(2026, 4, 1),
        raw_extracted={
            "source": "CATALOG_HS_CODE_MATRIX",
            "dataset": "hs_code_matrix",
            "effective_date": "2026-04-01",
            "catalog_rows": [
                {
                    "vehicle_type": "HYBRID",
                    "fuel_type": "PETROL",
                    "age_condition": "<=1",
                    "hs_code": "8703.40",
                    "capacity_min": 0,
                    "capacity_max": 1500,
                    "capacity_unit": "CC",
                    "cid_pct": 20,
                    "pal_pct": 0,
                    "cess_pct": 10,
                    "excise_unit_rate_lkr": 2450,
                    "min_excise_flat_rate_lkr": 0,
                }
            ],
        },
        status="PENDING",
        uploaded_by=admin_user.id,
    )
    db.add_all([global_gazette, hs_gazette])
    db.commit()
    db.refresh(global_gazette)
    db.refresh(hs_gazette)

    assert (
        client.post(
            f"/api/v1/gazette/{global_gazette.id}/approve", headers=admin_headers
        ).status_code
        == 200
    )
    assert (
        client.post(f"/api/v1/gazette/{hs_gazette.id}/approve", headers=admin_headers).status_code
        == 200
    )

    assert db.query(GlobalTaxParameter).filter(GlobalTaxParameter.is_active.is_(True)).count() == 6
    assert db.query(HSCodeMatrixRule).filter(HSCodeMatrixRule.is_active.is_(True)).count() == 1

    vehicle = Vehicle(
        stock_no="TEST-CATALOG-HYBRID",
        make="Honda",
        model="Vezel",
        year=date.today().year,
        price_jpy=4490000,
        engine_cc=1500,
        vehicle_type=VehicleType.SUV,
        fuel_type=FuelType.HYBRID,
        transmission=Transmission.AUTOMATIC,
        status=VehicleStatus.AVAILABLE,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    response = client.get(f"/api/v1/vehicles/{vehicle.id}/cost")

    assert response.status_code == 200
    data = response.json()
    assert float(data["customs_duty_lkr"]) > 0
    assert float(data["excise_duty_lkr"]) > 0
    assert float(data["vel_lkr"]) == 15000.0
    assert float(data["com_exm_sel_lkr"]) == 1750.0


def test_calculate_cost_uses_specific_electric_rule(client, db, admin_headers, admin_user):
    gazette = Gazette(
        gazette_no="2025/ELECTRIC-COST",
        effective_date=None,
        raw_extracted={
            "effective_date": "2025-02-01",
            "rules": [
                {
                    "vehicle_type": "Passenger Vehicle (BEV)",
                    "fuel_type": "Electric",
                    "category_code": "PASSENGER_VEHICLE_BEV",
                    "engine_min": 0,
                    "engine_max": 999999,
                    "power_kw_min": 50.01,
                    "power_kw_max": 100,
                    "age_years_min": 0,
                    "age_years_max": 3,
                    "customs_percent": 0,
                    "excise_percent": 0,
                    "excise_per_kw_amount": 24100,
                    "vat_percent": 15,
                    "pal_percent": 0,
                    "cess_percent": 0,
                    "apply_on": "CIF",
                }
            ],
        },
        status="PENDING",
        uploaded_by=admin_user.id,
    )
    db.add(gazette)
    db.commit()
    db.refresh(gazette)

    approve_response = client.post(f"/api/v1/gazette/{gazette.id}/approve", headers=admin_headers)
    assert approve_response.status_code == 200

    vehicle = Vehicle(
        stock_no="TEST-ELECTRIC-RULE",
        make="Nissan",
        model="Leaf",
        year=date.today().year - 2,
        price_jpy=1000000,
        engine_cc=0,
        motor_power_kw=75,
        vehicle_type=VehicleType.HATCHBACK,
        fuel_type=FuelType.ELECTRIC,
        transmission=Transmission.AUTOMATIC,
        status=VehicleStatus.AVAILABLE,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    response = client.get(f"/api/v1/vehicles/{vehicle.id}/cost")

    assert response.status_code == 200
    data = response.json()
    assert float(data["excise_duty_lkr"]) > 0
    assert float(data["vat_lkr"]) > 0


def test_calculate_cost_requires_motor_power_for_specific_electric_rule(
    client, db, admin_headers, admin_user
):
    gazette = Gazette(
        gazette_no="2025/ELECTRIC-MISSING-POWER",
        effective_date=None,
        raw_extracted={
            "effective_date": "2025-02-01",
            "rules": [
                {
                    "vehicle_type": "Passenger Vehicle (BEV)",
                    "fuel_type": "Electric",
                    "category_code": "PASSENGER_VEHICLE_BEV",
                    "engine_min": 0,
                    "engine_max": 999999,
                    "power_kw_min": 50.01,
                    "power_kw_max": 100,
                    "age_years_min": 0,
                    "age_years_max": 3,
                    "customs_percent": 0,
                    "excise_percent": 0,
                    "excise_per_kw_amount": 24100,
                    "vat_percent": 15,
                    "pal_percent": 0,
                    "cess_percent": 0,
                    "apply_on": "CIF",
                }
            ],
        },
        status="PENDING",
        uploaded_by=admin_user.id,
    )
    db.add(gazette)
    db.commit()
    db.refresh(gazette)

    approve_response = client.post(f"/api/v1/gazette/{gazette.id}/approve", headers=admin_headers)
    assert approve_response.status_code == 200

    vehicle = Vehicle(
        stock_no="TEST-ELECTRIC-NO-POWER",
        make="Nissan",
        model="Leaf",
        year=date.today().year - 2,
        price_jpy=1000000,
        engine_cc=0,
        vehicle_type=VehicleType.HATCHBACK,
        fuel_type=FuelType.ELECTRIC,
        transmission=Transmission.AUTOMATIC,
        status=VehicleStatus.AVAILABLE,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    response = client.get(f"/api/v1/vehicles/{vehicle.id}/cost")

    assert response.status_code == 400
    assert "Motor power (kW) is required" in response.json()["detail"]


# ============================================================================
# ADMIN ENDPOINTS TESTS (Require authentication)
# ============================================================================


def test_create_vehicle_unauthenticated(client, db):
    """Test creating a vehicle without authentication."""

    vehicle_data = {
        "stock_no": "TEST-NEW",
        "make": "Toyota",
        "model": "Test",
        "year": 2024,
        "price_jpy": 1000000,
    }

    response = client.post("/api/v1/vehicles", json=vehicle_data)

    # Should be forbidden (403) or unauthorized (401)
    assert response.status_code in [401, 403]


def test_scrape_now_admin_endpoint(client, admin_headers, mocker):
    """Admin endpoint should trigger scraper execution in a background thread."""

    run_now = mocker.patch("app.services.scraper.scheduler.scraper_scheduler.run_now")

    class ImmediateThread:
        def __init__(self, target, daemon=None):
            self.target = target
            self.daemon = daemon

        def start(self):
            self.target()

    mocker.patch("app.modules.vehicles.routes.threading.Thread", ImmediateThread)

    response = client.post("/api/v1/vehicles/scrape-now", headers=admin_headers)

    assert response.status_code == 202
    assert response.json()["status"] == "processing"
    run_now.assert_called_once()


def test_scheduler_change_detection_thresholds():
    """Scheduler should update only when CD-23 thresholds are crossed."""
    scheduler = ScraperScheduler()
    existing = Vehicle(
        stock_no="TH-001",
        chassis="TH-CH-001",
        make="Toyota",
        model="Corolla",
        year=2024,
        price_jpy=2000000,
        mileage_km=20000,
        status=VehicleStatus.AVAILABLE,
        image_url="https://example.com/v1.jpg",
    )

    no_change, fields = scheduler._should_update_vehicle(
        existing,
        {
            "price_jpy": 2080000,  # +4%
            "mileage_km": 20800,  # +800
            "status": "AVAILABLE",
            "image_url": "https://example.com/v1.jpg",
        },
    )
    assert no_change is False
    assert fields == []

    should_update, changed = scheduler._should_update_vehicle(
        existing,
        {
            "price_jpy": 2120000,  # +6%
            "mileage_km": 21200,  # +1200
            "status": "SOLD",
            "image_url": "https://example.com/v2.jpg",
        },
    )
    assert should_update is True
    assert "price_jpy" in changed
    assert "mileage_km" in changed
    assert "status" in changed
    assert "image_url" in changed


def test_scheduler_updates_identity_fields_when_stock_matches():
    scheduler = ScraperScheduler()
    existing = Vehicle(
        stock_no="74896",
        make="Honda",
        model="Vezel",
        year=2026,
        vehicle_type=VehicleType.SUV,
        body_type="SUV",
        status=VehicleStatus.AVAILABLE,
    )

    should_update, changed = scheduler._should_update_vehicle(
        existing,
        {
            "make": "Toyota",
            "model": "Corolla Axio",
            "year": 2025,
            "vehicle_type": "Sedan",
            "body_type": "Sedan",
            "status": "AVAILABLE",
        },
    )

    assert should_update is True
    assert "make" in changed
    assert "model" in changed
    assert "year" in changed
    assert "vehicle_type" in changed
    assert "body_type" in changed


def test_scheduler_scrape_mode_mock(mocker):
    scheduler = ScraperScheduler()
    mock_scrape = mocker.patch.object(
        scheduler._scraper, "scrape", return_value=[{"stock_no": "M-1"}]
    )
    live_scrape = mocker.patch.object(
        scheduler._live_scraper, "scrape", return_value=[{"stock_no": "L-1"}]
    )
    mocker.patch.dict(os.environ, {"CD23_SCRAPER_MODE": "mock"})

    rows = scheduler._scrape_vehicle_rows(count=1)

    assert rows[0]["stock_no"] == "M-1"
    mock_scrape.assert_called_once_with(count=1)
    live_scrape.assert_not_called()


def test_scheduler_scrape_mode_hybrid_falls_back_to_mock(mocker):
    scheduler = ScraperScheduler()
    live_scrape = mocker.patch.object(scheduler._live_scraper, "scrape", return_value=[])
    mock_scrape = mocker.patch.object(
        scheduler._scraper, "scrape", return_value=[{"stock_no": "M-2"}]
    )
    mocker.patch.dict(os.environ, {"CD23_SCRAPER_MODE": "hybrid"})

    rows = scheduler._scrape_vehicle_rows(count=1)

    assert rows[0]["stock_no"] == "M-2"
    live_scrape.assert_called_once_with(count=1)
    mock_scrape.assert_called_once_with(count=1)


def test_scheduler_existing_vehicle_lookup_does_not_collapse_same_make_model_year_price(db):
    scheduler = ScraperScheduler()
    existing = Vehicle(
        stock_no="EX-001",
        chassis="EX-CH-001",
        make="Honda",
        model="Vezel",
        year=2026,
        price_jpy=3990000,
        status=VehicleStatus.AVAILABLE,
        vehicle_url="https://example.com/old-vezel",
    )
    db.add(existing)
    db.commit()

    incoming = {
        "stock_no": "NEW-002",
        "chassis": "NEW-CH-002",
        "make": "Honda",
        "model": "Vezel",
        "year": 2026,
        "price_jpy": 3990000,
        "vehicle_url": "https://example.com/new-vezel",
    }

    assert scheduler._find_existing_vehicle(db, incoming) is None


def test_scheduler_existing_vehicle_lookup_ignores_placeholder_chassis(db):
    scheduler = ScraperScheduler()
    existing = Vehicle(
        stock_no="EX-PLACEHOLDER",
        chassis="****",
        make="Honda",
        model="Vezel",
        year=2026,
        price_jpy=3990000,
        status=VehicleStatus.AVAILABLE,
    )
    db.add(existing)
    db.commit()

    incoming = {
        "stock_no": "NEW-VEZEL",
        "chassis": "****",
        "vehicle_url": "https://example.com/new-vezel",
    }

    assert scheduler._find_existing_vehicle(db, incoming) is None


def test_scheduler_resolve_scrape_count_supports_all_keyword(mocker):
    mocker.patch.dict(os.environ, {"CD23_SCRAPE_COUNT": "all"})

    assert ScraperScheduler._resolve_scrape_count() == 0


def test_scheduler_resolve_scrape_count_defaults_on_invalid_value(mocker):
    mocker.patch.dict(os.environ, {"CD23_SCRAPE_COUNT": "not-a-number"})

    assert ScraperScheduler._resolve_scrape_count() == 10


def test_scheduler_normalize_row_enums_drops_invalid_enum_values():
    row = {
        "vehicle_type": "Cars",
        "body_type": "Cars",
        "steering": "Center",
        "drive": "Unknown",
        "transmission": "5MT",
        "fuel_type": "Diesel",
    }

    _normalize_row_enums(row)

    assert row["vehicle_type"] is None
    assert row["steering"] is None
    assert row["drive"] is None
    assert row["transmission"] is None
    assert row["fuel_type"] == "Diesel"


def test_auction_scraper_extract_listing_status():
    assert AuctionSiteScraper._extract_listing_status("Now On Sale FOB: 1,000,000") == "AVAILABLE"
    assert AuctionSiteScraper._extract_listing_status("Reserved Stock No. 123") == "RESERVED"
    assert AuctionSiteScraper._extract_listing_status("Sold Out") == "SOLD"


def test_scheduler_should_import_row_requires_price_and_available_status():
    assert ScraperScheduler._should_import_row({"price_jpy": 1000, "status": "AVAILABLE"}) is True
    assert ScraperScheduler._should_import_row({"price_jpy": 0, "status": "AVAILABLE"}) is False
    assert ScraperScheduler._should_import_row({"price_jpy": None, "status": "AVAILABLE"}) is False
    assert ScraperScheduler._should_import_row({"price_jpy": 1000, "status": "SOLD"}) is False


def test_create_vehicle_authenticated(client, db, admin_headers):
    """Test creating a vehicle with admin authentication."""

    vehicle_data = {
        "stock_no": "TEST-NEW",
        "make": "Toyota",
        "model": "Test Car",
        "year": 2024,
        "price_jpy": 1000000,
        "mileage_km": 10000,
        "engine_cc": 1500,
        "fuel_type": "Gasoline",
        "transmission": "Automatic",
        "status": "AVAILABLE",
    }

    response = client.post("/api/v1/vehicles", json=vehicle_data, headers=admin_headers)

    assert response.status_code == 201
    data = response.json()
    assert data["stock_no"] == "TEST-NEW"
    assert data["make"] == "Toyota"
    assert data["model"] == "Test Car"


def test_create_vehicle_duplicate_stock_no(client, db, admin_headers):
    """Test creating a vehicle with duplicate stock_no."""

    # Create first vehicle
    vehicle = Vehicle(
        stock_no="TEST-001",
        make="Toyota",
        model="Prius",
        year=2020,
        price_jpy=1850000,
    )
    db.add(vehicle)
    db.commit()

    # Try to create duplicate
    vehicle_data = {
        "stock_no": "TEST-001",
        "make": "Honda",
        "model": "Fit",
        "year": 2021,
        "price_jpy": 1500000,
    }

    response = client.post("/api/v1/vehicles", json=vehicle_data, headers=admin_headers)

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


def test_update_vehicle(client, db, admin_headers):
    """Test updating a vehicle."""

    # Create test vehicle
    vehicle = Vehicle(
        stock_no="TEST-001",
        make="Toyota",
        model="Prius",
        year=2020,
        price_jpy=1850000,
        status=VehicleStatus.AVAILABLE,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    # Update vehicle
    update_data = {"price_jpy": 2000000, "status": "RESERVED"}

    response = client.patch(
        f"/api/v1/vehicles/{vehicle.id}", json=update_data, headers=admin_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert float(data["price_jpy"]) == 2000000
    assert data["status"] == "RESERVED"


def test_delete_vehicle(client, db, admin_headers):
    """Test deleting a vehicle."""

    # Create test vehicle
    vehicle = Vehicle(
        stock_no="TEST-001",
        make="Toyota",
        model="Prius",
        year=2020,
        price_jpy=1850000,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    vehicle_id = vehicle.id

    # Delete vehicle
    response = client.delete(f"/api/v1/vehicles/{vehicle_id}", headers=admin_headers)

    assert response.status_code == 204

    # Verify deletion
    response = client.get(f"/api/v1/vehicles/{vehicle_id}")
    assert response.status_code == 404


def test_delete_vehicle_unauthenticated(client, db):
    """Test deleting a vehicle without authentication."""

    # Create test vehicle
    vehicle = Vehicle(
        stock_no="TEST-001",
        make="Toyota",
        model="Prius",
        year=2020,
        price_jpy=1850000,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    # Try to delete without auth
    response = client.delete(f"/api/v1/vehicles/{vehicle.id}")

    # Should be forbidden (403) or unauthorized (401)
    assert response.status_code in [401, 403]
