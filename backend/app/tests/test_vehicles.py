<<<<<<< HEAD
# backend/app/tests/test_vehicles.py

"""
Test vehicle endpoints.
Author: Parindra Chameekara
Epic: CD-E3 - Vehicle Management System
Story: CD-130 - Vehicle Search & Filter API
"""

from app.modules.vehicles.models import (
    Drive,
    FuelType,
    Steering,
    Transmission,
    Vehicle,
    VehicleStatus,
)

# ============================================================================
# PUBLIC ENDPOINTS TESTS (No authentication required)
# ============================================================================
=======
# backend/tests/test_vehicles.py

"""
Test vehicle endpoints.
"""

from app.modules.vehicles.models import FuelType, Transmission, Vehicle, VehicleStatus
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7


def test_get_vehicles_empty(client, db):
    """Test getting vehicles when none exist."""
    response = client.get("/api/v1/vehicles")

    assert response.status_code == 200
    data = response.json()
<<<<<<< HEAD
    assert data["pagination"]["total"] == 0
    assert data["vehicles"] == []
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["limit"] == 20
    assert data["pagination"]["total_pages"] == 0
=======
    assert data["total"] == 0
    assert data["vehicles"] == []
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7


def test_get_vehicles_with_data(client, db):
    """Test getting vehicles when data exists."""

    # Create test vehicle
    vehicle = Vehicle(
<<<<<<< HEAD
        stock_no="TEST-001",
=======
        auction_id="TEST-001",
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
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
<<<<<<< HEAD
    assert data["pagination"]["total"] == 1
    assert len(data["vehicles"]) == 1
    assert data["vehicles"][0]["make"] == "Toyota"
    assert data["vehicles"][0]["model"] == "Prius"
    assert data["vehicles"][0]["year"] == 2020
    assert data["vehicles"][0]["stock_no"] == "TEST-001"


def test_search_vehicles_by_make(client, db):
    """Test vehicle search by make."""

    # Create test vehicles
    vehicles = [
        Vehicle(stock_no="T1", make="Toyota", model="Prius", year=2020, price_jpy=1850000),
        Vehicle(stock_no="T2", make="Toyota", model="Aqua", year=2019, price_jpy=1250000),
        Vehicle(stock_no="H1", make="Honda", model="Fit", year=2020, price_jpy=1350000),
=======
    assert data["total"] == 1
    assert len(data["vehicles"]) == 1
    assert data["vehicles"][0]["make"] == "Toyota"
    assert data["vehicles"][0]["model"] == "Prius"


def test_search_vehicles(client, db):
    """Test vehicle search functionality."""

    # Create test vehicles
    vehicles = [
        Vehicle(auction_id="T1", make="Toyota", model="Prius", year=2020, price_jpy=1850000),
        Vehicle(auction_id="T2", make="Toyota", model="Aqua", year=2019, price_jpy=1250000),
        Vehicle(auction_id="H1", make="Honda", model="Fit", year=2020, price_jpy=1350000),
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
    ]

    for v in vehicles:
        db.add(v)
    db.commit()

    # Search for Toyota
    response = client.get("/api/v1/vehicles", params={"search": "Toyota"})

    assert response.status_code == 200
    data = response.json()
<<<<<<< HEAD
    assert data["pagination"]["total"] == 2
=======
    assert data["total"] == 2
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7

    # Search for Honda
    response = client.get("/api/v1/vehicles", params={"search": "Honda"})

    assert response.status_code == 200
    data = response.json()
<<<<<<< HEAD
    assert data["pagination"]["total"] == 1
=======
    assert data["total"] == 1
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
