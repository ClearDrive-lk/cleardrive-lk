# backend/app/tests/test_vehicles.py

"""
Test vehicle endpoints.
Author: Parindra Chameekara
Epic: CD-E3 - Vehicle Management System
Story: CD-130 - Vehicle Search & Filter API
"""

from app.modules.vehicles.models import (
    FuelType,
    Transmission,
    Vehicle,
    VehicleStatus,
)


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
