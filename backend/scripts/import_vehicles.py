"""
Import vehicles from JSON dataset into the database.
Story: CD-20.3
"""

import json
import logging
import sys
from decimal import Decimal
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.modules.vehicles.models import Drive, FuelType, Steering, Transmission, Vehicle, VehicleStatus, VehicleType

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def _map_fuel(v: str | None):
    if not v:
        return None
    s = v.strip().lower()
    if s in {"petrol", "gasoline"}:
        return FuelType.GASOLINE.value
    if s in {"hybrid", "petrol/hybrid", "gasoline/hybrid"}:
        return FuelType.HYBRID.value
    if s == "diesel":
        return FuelType.DIESEL.value
    if s == "electric":
        return FuelType.ELECTRIC.value
    return None


def _map_transmission(v: str | None):
    if not v:
        return None
    s = v.strip().lower()
    if s == "automatic":
        return Transmission.AUTOMATIC.value
    if s == "manual":
        return Transmission.MANUAL.value
    if s == "cvt":
        return Transmission.CVT.value
    return None


def _map_vehicle_type(v: str | None):
    if not v:
        return None
    s = v.strip().lower()
    m = {
        "sedan": VehicleType.SEDAN.value,
        "suv": VehicleType.SUV.value,
        "hatchback": VehicleType.HATCHBACK.value,
        "van/minivan": VehicleType.VAN_MINIVAN.value,
        "wagon": VehicleType.WAGON.value,
        "pickup": VehicleType.PICKUP.value,
        "coupe": VehicleType.COUPE.value,
        "convertible": VehicleType.CONVERTIBLE.value,
        "bikes": VehicleType.BIKES.value,
        "machinery": VehicleType.MACHINERY.value,
    }
    return m.get(s)


def _map_drive(v: str | None):
    if not v:
        return None
    s = v.strip().upper()
    if s == "2WD":
        return Drive.TWO_WD.value
    if s == "4WD":
        return Drive.FOUR_WD.value
    if s == "AWD":
        return Drive.AWD.value
    if s == "FWD":
        return Drive.TWO_WD.value
    return None


def import_vehicles() -> None:
    json_path = Path(__file__).parent.parent / "data" / "vehicles.json"
    if not json_path.exists():
        raise FileNotFoundError(f"Missing dataset: {json_path}")

    data = json.loads(json_path.read_text(encoding="utf-8"))
    vehicles_data = data.get("vehicles", []) if isinstance(data, dict) else data

    imported, skipped = 0, 0
    with SessionLocal() as db:
        for row in vehicles_data:
            stock_no = row.get("stock_no")
            if not stock_no:
                continue

            exists = db.query(Vehicle).filter(Vehicle.stock_no == stock_no).first()
            if exists:
                skipped += 1
                continue

            chassis = row.get("chassis") or row.get("chassis_number")
            images = row.get("images") or []
            primary_image = row.get("image_url") or (images[0] if images else None)

            vehicle = Vehicle(
                stock_no=stock_no,
                chassis=chassis,
                make=row.get("make"),
                model=row.get("model"),
                reg_year=row.get("reg_year"),
                year=row.get("year"),
                vehicle_type=_map_vehicle_type(row.get("vehicle_type") or row.get("body_type")),
                body_type=row.get("body_type"),
                grade=row.get("grade") or row.get("auction_grade"),
                price_jpy=Decimal(str(row.get("price_jpy"))),
                mileage_km=row.get("mileage_km"),
                engine_cc=row.get("engine_cc"),
                engine_model=row.get("engine_model"),
                fuel_type=_map_fuel(row.get("fuel_type")),
                transmission=_map_transmission(row.get("transmission")),
                steering=Steering.RIGHT_HAND.value,
                drive=_map_drive(row.get("drive") or row.get("drive_type")),
                seats=row.get("seats") or row.get("seating_capacity"),
                doors=row.get("doors"),
                color=row.get("color"),
                location=row.get("location"),
                dimensions=row.get("dimensions"),
                length_cm=row.get("length_cm"),
                width_cm=row.get("width_cm"),
                height_cm=row.get("height_cm"),
                m3_size=Decimal(str(row["m3_size"])) if row.get("m3_size") is not None else None,
                options=row.get("options") or ", ".join(row.get("features", [])),
                other_remarks=row.get("description"),
                image_url=primary_image,
                vehicle_url=row.get("vehicle_url"),
                model_no=row.get("model_no"),
                status=VehicleStatus.AVAILABLE.value,
            )

            db.add(vehicle)
            imported += 1

        db.commit()

    logging.info("Import complete: imported=%s skipped=%s total=%s", imported, skipped, len(vehicles_data))


if __name__ == "__main__":
    import_vehicles()
