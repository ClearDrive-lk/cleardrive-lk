# backend/scripts/init_db.py

"""
Database initialization script.
Creates initial admin user and sample data.
"""

import logging
from typing import cast

from app.core.config import settings
from app.core.database import SessionLocal
from app.modules.auth.models import Role, User
from app.modules.vehicles.models import FuelType, Transmission, Vehicle, VehicleStatus
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_admin_user(db: Session) -> User:
    """Create initial admin user."""

    admin_emails = settings.ADMIN_EMAILS.split(",")
    first_admin_email = admin_emails[0].strip()

    # Check if admin already exists
    existing_admin = db.query(User).filter(User.email == first_admin_email).first()
    if existing_admin:
        logger.info(f"Admin user already exists: {first_admin_email}")
        return cast(User, existing_admin)

    # Create admin user
    admin_user = User(
        email=first_admin_email,
        name="System Administrator",
        role=Role.ADMIN,
    )

    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    logger.info(f"✅ Created admin user: {first_admin_email}")
    return admin_user


def create_sample_vehicles(db: Session) -> None:
    """Create sample vehicles for testing."""

    # Check if vehicles already exist
    existing_count = db.query(Vehicle).count()
    if existing_count >= 20:
        logger.info(f"Sample vehicles already exist: {existing_count} vehicles")
        return

    sample_vehicles = [
        # Toyota Models
        {
            "auction_id": "AUC-2025-001",
            "make": "Toyota",
            "model": "Prius",
            "year": 2020,
            "price_jpy": 1850000,
            "mileage_km": 35000,
            "engine_cc": 1800,
            "fuel_type": FuelType.HYBRID,
            "transmission": Transmission.AUTOMATIC,
            "auction_grade": "4.5",
            "color": "Silver",
            "status": VehicleStatus.AVAILABLE,
        },
        {
            "auction_id": "AUC-2025-002",
            "make": "Toyota",
            "model": "Aqua",
            "year": 2018,
            "price_jpy": 1050000,
            "mileage_km": 55000,
            "engine_cc": 1500,
            "fuel_type": FuelType.HYBRID,
            "transmission": Transmission.AUTOMATIC,
            "auction_grade": "3.5",
            "color": "Red",
            "status": VehicleStatus.AVAILABLE,
        },
        {
            "auction_id": "AUC-2025-003",
            "make": "Toyota",
            "model": "Corolla Axio",
            "year": 2019,
            "price_jpy": 1450000,
            "mileage_km": 42000,
            "engine_cc": 1500,
            "fuel_type": FuelType.HYBRID,
            "transmission": Transmission.AUTOMATIC,
            "auction_grade": "4.0",
            "color": "White",
            "status": VehicleStatus.AVAILABLE,
        },
        {
            "auction_id": "AUC-2025-004",
            "make": "Toyota",
            "model": "Vitz",
            "year": 2017,
            "price_jpy": 850000,
            "mileage_km": 68000,
            "engine_cc": 1000,
            "fuel_type": FuelType.PETROL,
            "transmission": Transmission.AUTOMATIC,
            "auction_grade": "3.0",
            "color": "Blue",
            "status": VehicleStatus.AVAILABLE,
        },
        # Honda Models
        {
            "auction_id": "AUC-2025-005",
            "make": "Honda",
            "model": "Fit",
            "year": 2019,
            "price_jpy": 1250000,
            "mileage_km": 42000,
            "engine_cc": 1300,
            "fuel_type": FuelType.PETROL,
            "transmission": Transmission.AUTOMATIC,
            "auction_grade": "4.0",
            "color": "White",
            "status": VehicleStatus.AVAILABLE,
        },
        {
            "auction_id": "AUC-2025-006",
            "make": "Honda",
            "model": "Vezel",
            "year": 2020,
            "price_jpy": 1950000,
            "mileage_km": 28000,
            "engine_cc": 1500,
            "fuel_type": FuelType.HYBRID,
            "transmission": Transmission.AUTOMATIC,
            "auction_grade": "4.5",
            "color": "Black",
            "status": VehicleStatus.AVAILABLE,
        },
        {
            "auction_id": "AUC-2025-007",
            "make": "Honda",
            "model": "Grace",
            "year": 2018,
            "price_jpy": 1350000,
            "mileage_km": 48000,
            "engine_cc": 1500,
            "fuel_type": FuelType.HYBRID,
            "transmission": Transmission.AUTOMATIC,
            "auction_grade": "4.0",
            "color": "Silver",
            "status": VehicleStatus.AVAILABLE,
        },
        # Nissan Models
        {
            "auction_id": "AUC-2025-008",
            "make": "Nissan",
            "model": "Leaf",
            "year": 2021,
            "price_jpy": 2100000,
            "mileage_km": 28000,
            "engine_cc": 0,  # Electric
            "fuel_type": FuelType.ELECTRIC,
            "transmission": Transmission.AUTOMATIC,
            "auction_grade": "5.0",
            "color": "Blue",
            "status": VehicleStatus.AVAILABLE,
        },
        {
            "auction_id": "AUC-2025-009",
            "make": "Nissan",
            "model": "Note",
            "year": 2019,
            "price_jpy": 1180000,
            "mileage_km": 45000,
            "engine_cc": 1200,
            "fuel_type": FuelType.PETROL,
            "transmission": Transmission.AUTOMATIC,
            "auction_grade": "3.5",
            "color": "Red",
            "status": VehicleStatus.AVAILABLE,
        },
        {
            "auction_id": "AUC-2025-010",
            "make": "Nissan",
            "model": "Serena",
            "year": 2018,
            "price_jpy": 1680000,
            "mileage_km": 62000,
            "engine_cc": 2000,
            "fuel_type": FuelType.PETROL,
            "transmission": Transmission.AUTOMATIC,
            "auction_grade": "3.5",
            "color": "White",
            "status": VehicleStatus.AVAILABLE,
        },
        # Mazda Models
        {
            "auction_id": "AUC-2025-011",
            "make": "Mazda",
            "model": "Demio",
            "year": 2017,
            "price_jpy": 950000,
            "mileage_km": 68000,
            "engine_cc": 1300,
            "fuel_type": FuelType.PETROL,
            "transmission": Transmission.AUTOMATIC,
            "auction_grade": "3.0",
            "color": "Black",
            "status": VehicleStatus.AVAILABLE,
        },
        {
            "auction_id": "AUC-2025-012",
            "make": "Mazda",
            "model": "Axela",
            "year": 2019,
            "price_jpy": 1450000,
            "mileage_km": 38000,
            "engine_cc": 1500,
            "fuel_type": FuelType.PETROL,
            "transmission": Transmission.AUTOMATIC,
            "auction_grade": "4.0",
            "color": "Red",
            "status": VehicleStatus.AVAILABLE,
        },
        # Suzuki Models
        {
            "auction_id": "AUC-2025-013",
            "make": "Suzuki",
            "model": "Swift",
            "year": 2018,
            "price_jpy": 920000,
            "mileage_km": 52000,
            "engine_cc": 1200,
            "fuel_type": FuelType.PETROL,
            "transmission": Transmission.AUTOMATIC,
            "auction_grade": "3.5",
            "color": "White",
            "status": VehicleStatus.AVAILABLE,
        },
        {
            "auction_id": "AUC-2025-014",
            "make": "Suzuki",
            "model": "Wagon R",
            "year": 2017,
            "price_jpy": 780000,
            "mileage_km": 72000,
            "engine_cc": 660,
            "fuel_type": FuelType.PETROL,
            "transmission": Transmission.AUTOMATIC,
            "auction_grade": "3.0",
            "color": "Silver",
            "status": VehicleStatus.AVAILABLE,
        },
        # Mitsubishi Models
        {
            "auction_id": "AUC-2025-015",
            "make": "Mitsubishi",
            "model": "Outlander PHEV",
            "year": 2020,
            "price_jpy": 2350000,
            "mileage_km": 32000,
            "engine_cc": 2400,
            "fuel_type": FuelType.HYBRID,
            "transmission": Transmission.AUTOMATIC,
            "auction_grade": "4.5",
            "color": "Black",
            "status": VehicleStatus.AVAILABLE,
        },
        # Daihatsu Models
        {
            "auction_id": "AUC-2025-016",
            "make": "Daihatsu",
            "model": "Move",
            "year": 2017,
            "price_jpy": 680000,
            "mileage_km": 78000,
            "engine_cc": 660,
            "fuel_type": FuelType.PETROL,
            "transmission": Transmission.AUTOMATIC,
            "auction_grade": "3.0",
            "color": "Blue",
            "status": VehicleStatus.AVAILABLE,
        },
        {
            "auction_id": "AUC-2025-017",
            "make": "Daihatsu",
            "model": "Tanto",
            "year": 2018,
            "price_jpy": 850000,
            "mileage_km": 58000,
            "engine_cc": 660,
            "fuel_type": FuelType.PETROL,
            "transmission": Transmission.AUTOMATIC,
            "auction_grade": "3.5",
            "color": "White",
            "status": VehicleStatus.AVAILABLE,
        },
        # Premium/Luxury Models
        {
            "auction_id": "AUC-2025-018",
            "make": "Lexus",
            "model": "CT200h",
            "year": 2019,
            "price_jpy": 2150000,
            "mileage_km": 35000,
            "engine_cc": 1800,
            "fuel_type": FuelType.HYBRID,
            "transmission": Transmission.AUTOMATIC,
            "auction_grade": "4.5",
            "color": "Silver",
            "status": VehicleStatus.AVAILABLE,
        },
        {
            "auction_id": "AUC-2025-019",
            "make": "BMW",
            "model": "3 Series",
            "year": 2018,
            "price_jpy": 2850000,
            "mileage_km": 42000,
            "engine_cc": 2000,
            "fuel_type": FuelType.PETROL,
            "transmission": Transmission.AUTOMATIC,
            "auction_grade": "4.0",
            "color": "Black",
            "status": VehicleStatus.AVAILABLE,
        },
        {
            "auction_id": "AUC-2025-020",
            "make": "Mercedes-Benz",
            "model": "C-Class",
            "year": 2019,
            "price_jpy": 3200000,
            "mileage_km": 38000,
            "engine_cc": 2000,
            "fuel_type": FuelType.PETROL,
            "transmission": Transmission.AUTOMATIC,
            "auction_grade": "4.5",
            "color": "White",
            "status": VehicleStatus.AVAILABLE,
        },
    ]

    # Only add vehicles that don't exist
    for vehicle_data in sample_vehicles:
        existing = (
            db.query(Vehicle).filter(Vehicle.auction_id == vehicle_data["auction_id"]).first()
        )

        if not existing:
            vehicle = Vehicle(**vehicle_data)
            db.add(vehicle)

    db.commit()

    # Count total vehicles
    total = db.query(Vehicle).count()
    logger.info(f"✅ Vehicle database ready: {total} vehicles available")


def init_database():
    """Initialize database with admin user and sample data."""

    logger.info("🚀 Starting database initialization...")

    # Create database session
    db = SessionLocal()

    try:
        # Create admin user
        create_admin_user(db)

        # Create sample vehicles
        create_sample_vehicles(db)

        logger.info("✅ Database initialization complete!")

    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
