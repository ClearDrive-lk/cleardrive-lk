"""Seed minimal gazette + tax rules for local development.

This creates a single approved gazette and broad tax rules so the
vehicle cost calculator can return data in a fresh dev database.
"""

from __future__ import annotations

import os
from datetime import date
from decimal import Decimal

from app.core.database import SessionLocal
from app import modules as _modules  # noqa: F401
from app.models.gazette import (
    ApplyOn,
    Gazette,
    GazetteStatus,
    TaxFuelType,
    TaxRule,
    TaxVehicleType,
)


def main() -> None:
    db = SessionLocal()
    try:
        existing = db.query(TaxRule).count()
        if existing > 0:
            print(f"Seed skipped: tax_rules already has {existing} rows.")
            return

        gazette_no = os.getenv("GAZETTE_SEED_NO", "DEV/SEED/2026")
        effective = date.today()
        gazette = Gazette(
            gazette_no=gazette_no,
            effective_date=effective,
            raw_extracted={},
            status=GazetteStatus.APPROVED.value,
        )
        db.add(gazette)
        db.commit()
        db.refresh(gazette)

        base_customs = Decimal("25.0")
        base_excise = Decimal("50.0")
        base_vat = Decimal("15.0")
        base_pal = Decimal("7.5")
        base_surcharge = Decimal("0.0")
        base_cess = Decimal("0.0")

        vehicle_types = [value for value in TaxVehicleType]
        fuel_types = [value for value in TaxFuelType]
        created = 0

        for vehicle_type in vehicle_types:
            for fuel_type in fuel_types:
                excise = base_excise
                if fuel_type.value == TaxFuelType.ELECTRIC.value:
                    excise = Decimal("10.0")
                rule = TaxRule(
                    gazette_id=gazette.id,
                    vehicle_type=vehicle_type.value,
                    fuel_type=fuel_type.value,
                    engine_min=0,
                    engine_max=999999,
                    customs_percent=base_customs,
                    surcharge_percent=base_surcharge,
                    excise_percent=excise,
                    vat_percent=base_vat,
                    pal_percent=base_pal,
                    cess_percent=base_cess,
                    apply_on=ApplyOn.CIF_PLUS_CUSTOMS.value,
                    effective_date=effective,
                    is_active=True,
                )
                db.add(rule)
                created += 1

        db.commit()
        print(f"Seeded gazette {gazette_no} with {created} tax rules.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
