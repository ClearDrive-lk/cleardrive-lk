# backend/scripts/import_static_vehicles.py

"""
Import static vehicle dataset into database.
Author: Parindra Chameekara
Epic: CD-E3 - Vehicle Management System
Story: CD-120 - Static Vehicle Dataset
Usage: python scripts/import_static_vehicles.py
"""

import json
import logging
import sys
from decimal import Decimal
from pathlib import Path

# Add backend directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.modules.vehicles.models import (
    Drive,
    FuelType,
    Steering,
    Transmission,
    Vehicle,
    VehicleStatus,
    VehicleType,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def map_fuel_type(fuel_type_str):
    """Map fuel type string to enum value."""
    if not fuel_type_str:
        return None

    fuel_type_str = fuel_type_str.strip()

    # Direct mapping
    fuel_type_map = {
        "Gasoline": FuelType.GASOLINE,
        "Diesel": FuelType.DIESEL,
        "Gasoline/hybrid": FuelType.HYBRID,
        "Hybrid": FuelType.HYBRID,
        "Electric": FuelType.ELECTRIC,
        "Plugin Hybrid": FuelType.PLUGIN_HYBRID,
    }

    return fuel_type_map.get(fuel_type_str)


def map_transmission(transmission_str):
    """Map transmission string to enum value."""
    if not transmission_str:
        return None

    transmission_str = transmission_str.strip()

    transmission_map = {
        "Automatic": Transmission.AUTOMATIC,
        "Manual": Transmission.MANUAL,
        "CVT": Transmission.CVT,
    }

    return transmission_map.get(transmission_str)


def map_vehicle_type(vehicle_type_str):
    """Map vehicle type string to enum value."""
    if not vehicle_type_str:
        return None

    vehicle_type_str = vehicle_type_str.strip()

    vehicle_type_map = {
        "Sedan": VehicleType.SEDAN,
        "SUV": VehicleType.SUV,
        "Hatchback": VehicleType.HATCHBACK,
        "Van/minivan": VehicleType.VAN_MINIVAN,
        "Wagon": VehicleType.WAGON,
        "Pickup": VehicleType.PICKUP,
        "Coupe": VehicleType.COUPE,
        "Convertible": VehicleType.CONVERTIBLE,
        "Bikes": VehicleType.BIKES,
        "Machinery": VehicleType.MACHINERY,
    }

    return vehicle_type_map.get(vehicle_type_str)


def map_steering(steering_str):
    """Map steering string to enum value."""
    if not steering_str:
        return None

    steering_str = steering_str.strip()

    steering_map = {
        "Right Hand": Steering.RIGHT_HAND,
        "Left Hand": Steering.LEFT_HAND,
    }

    return steering_map.get(steering_str)


def map_drive(drive_str):
    """Map drive string to enum value."""
    if not drive_str:
        return None

    drive_str = drive_str.strip()

    drive_map = {
        "2WD": Drive.TWO_WD,
        "4WD": Drive.FOUR_WD,
        "AWD": Drive.AWD,
    }

    return drive_map.get(drive_str)


def map_status(status_str):
    """Map status string to enum value."""
    if not status_str:
        return VehicleStatus.AVAILABLE

    status_str = status_str.strip().upper()

    status_map = {
        "AVAILABLE": VehicleStatus.AVAILABLE,
        "RESERVED": VehicleStatus.RESERVED,
        "SOLD": VehicleStatus.SOLD,
    }

    return status_map.get(status_str, VehicleStatus.AVAILABLE)


def import_vehicles():
    """Import vehicles from static JSON file."""

    # Load JSON data
    json_path = Path(__file__).parent.parent / "data" / "static_vehicles.json"

    if not json_path.exists():
        logging.error(f"File not found at {json_path}")
        logging.error("Please create the file first!")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Handle both formats: {"vehicles": [...]} or [...]
    if isinstance(data, dict) and "vehicles" in data:
        vehicles_data = data["vehicles"]
    elif isinstance(data, list):
        vehicles_data = data
    else:
        logging.error("Invalid JSON format in static_vehicles.json")
        return

    logging.info("=" * 70)
    logging.info("📥 IMPORTING STATIC VEHICLE DATASET")
    logging.info(f"Found {len(vehicles_data)} vehicles in JSON file")
    logging.info("=" * 70)

    imported = 0
    skipped = 0
    errors = 0

    with SessionLocal() as db:
        for idx, vehicle_data in enumerate(vehicles_data, 1):
            try:
                stock_no = vehicle_data.get("stock_no")

                if not stock_no:
                    logging.error(f"[{idx:3d}] Missing stock_no")
                    errors += 1
                    continue

                # Check if vehicle already exists
                existing = db.query(Vehicle).filter(Vehicle.stock_no == stock_no).first()

                if existing:
                    logging.info(f"[{idx:3d}] Skipped: {stock_no} (already exists)")
                    skipped += 1
                    continue

                # Map enums
                fuel_type = map_fuel_type(vehicle_data.get("fuel_type"))
                transmission = map_transmission(vehicle_data.get("transmission"))
                vehicle_type = map_vehicle_type(vehicle_data.get("vehicle_type"))
                steering = map_steering(vehicle_data.get("steering"))
                drive = map_drive(vehicle_data.get("drive"))
                status = map_status(vehicle_data.get("status"))

                # Extract year from reg_year if year is missing
                year = vehicle_data.get("year")
                if not year and vehicle_data.get("reg_year"):
                    reg_year_str = str(vehicle_data["reg_year"])
                    if "/" in reg_year_str:
                        year = int(reg_year_str.split("/")[0])
                    else:
                        year = int(reg_year_str)

                # Create new vehicle
                vehicle = Vehicle(
                    stock_no=stock_no,
                    chassis=vehicle_data.get("chassis"),
                    make=vehicle_data["make"],
                    model=vehicle_data["model"],
                    reg_year=vehicle_data.get("reg_year"),
                    year=year,
                    vehicle_type=vehicle_type,
                    body_type=vehicle_data.get("body_type"),
                    grade=vehicle_data.get("grade"),
                    price_jpy=Decimal(str(vehicle_data["price_jpy"])),
                    mileage_km=vehicle_data.get("mileage_km"),
                    engine_cc=vehicle_data.get("engine_cc"),
                    engine_model=vehicle_data.get("engine_model"),
                    fuel_type=fuel_type,
                    transmission=transmission,
                    steering=steering,
                    drive=drive,
                    seats=vehicle_data.get("seats"),
                    doors=vehicle_data.get("doors"),
                    color=vehicle_data.get("color"),
                    location=vehicle_data.get("location"),
                    dimensions=vehicle_data.get("dimensions"),
                    length_cm=vehicle_data.get("length_cm"),
                    width_cm=vehicle_data.get("width_cm"),
                    height_cm=vehicle_data.get("height_cm"),
                    m3_size=Decimal(str(vehicle_data["m3_size"]))
                    if vehicle_data.get("m3_size")
                    else None,
                    options=vehicle_data.get("options"),
                    other_remarks=vehicle_data.get("other_remarks"),
                    image_url=vehicle_data.get("image_url"),
                    vehicle_url=vehicle_data.get("vehicle_url"),
                    model_no=vehicle_data.get("model_no"),
                    status=status,
                )

                db.add(vehicle)
                db.commit()

                logging.info(
                    f"[{idx:3d}] Imported: {vehicle.make} {vehicle.model} ({vehicle.year}) - Stock#{vehicle.stock_no}"
                )
                imported += 1

            except KeyError as e:
                logging.error(
                    f"[{idx:3d}] Missing required field {e} for stock_no {vehicle_data.get('stock_no', 'UNKNOWN')}"
                )
                db.rollback()
                errors += 1
                continue

            except Exception as e:
                logging.error(
                    f"[{idx:3d}] Error importing {vehicle_data.get('stock_no', 'UNKNOWN')}: {e}"
                )
                db.rollback()
                errors += 1
                continue

    logging.info("=" * 70)
    logging.info("✅ IMPORT COMPLETE!")
    logging.info("=" * 70)
    logging.info(f"   ✅ Imported: {imported}")
    logging.info(f"   ⏭️  Skipped:  {skipped}")
    logging.info(f"   ❌ Errors:   {errors}")
    logging.info(f"   📊 Total:    {len(vehicles_data)}")
    logging.info("=" * 70)


if __name__ == "__main__":
    import_vehicles()
