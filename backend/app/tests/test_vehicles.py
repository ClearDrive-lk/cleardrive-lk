# backend/app/tests/test_vehicles.py

"""
Test vehicle endpoints.
Author: Parindra Chameekara
Epic: CD-E3 - Vehicle Management System
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


def test_calculate_cost(client, db):
    """Test calculating cost for a vehicle."""

    # Create test vehicle
    vehicle = Vehicle(
        stock_no="TEST-001",
        make="Toyota",
        model="Prius",
        year=2020,
        price_jpy=2000000,
        mileage_km=35000,
        engine_cc=1800,
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
    assert "shipping_cost_lkr" in data
    assert "customs_duty_lkr" in data
    assert "vat_lkr" in data
    assert "total_cost_lkr" in data
    assert "vehicle_percentage" in data
    assert "taxes_percentage" in data
    assert "fees_percentage" in data

    # Check values are positive
    assert float(data["vehicle_price_jpy"]) == 2000000
    assert float(data["total_cost_lkr"]) > 0


def test_calculate_cost_custom_exchange_rate(client, db):
    """Test calculating cost with custom exchange rate."""

    # Create test vehicle
    vehicle = Vehicle(
        stock_no="TEST-001",
        make="Toyota",
        model="Prius",
        year=2020,
        price_jpy=1000000,
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
