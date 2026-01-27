# backend/scripts/init_db.py

"""
Database initialization script.
Creates initial admin user and sample data.
"""

import asyncio
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.modules.auth.models import User, Role
from app.modules.vehicles.models import Vehicle, VehicleStatus, FuelType, Transmission
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_admin_user(db: Session) -> User:
    """Create initial admin user."""
    
    admin_emails = settings.ADMIN_EMAILS.split(',')
    first_admin_email = admin_emails[0].strip()
    
    # Check if admin already exists
    existing_admin = db.query(User).filter(User.email == first_admin_email).first()
    if existing_admin:
        logger.info(f"Admin user already exists: {first_admin_email}")
        return existing_admin
    
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
    if existing_count > 0:
        logger.info(f"Sample vehicles already exist: {existing_count} vehicles")
        return
    
    sample_vehicles = [
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
            "auction_id": "AUC-2025-003",
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
            "auction_id": "AUC-2025-004",
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
            "auction_id": "AUC-2025-005",
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
    ]
    
    for vehicle_data in sample_vehicles:
        vehicle = Vehicle(**vehicle_data)
        db.add(vehicle)
    
    db.commit()
    logger.info(f"✅ Created {len(sample_vehicles)} sample vehicles")


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