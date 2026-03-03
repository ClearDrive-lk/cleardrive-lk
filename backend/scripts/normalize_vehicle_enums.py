"""
Normalize legacy vehicle enum-like string values in the vehicles table.

Usage:
  python scripts/normalize_vehicle_enums.py --mode local --dry-run
  python scripts/normalize_vehicle_enums.py --mode local --apply
  python scripts/normalize_vehicle_enums.py --mode supabase --apply
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value and not (value.startswith("'") or value.startswith('"')):
            value = value.split("#", 1)[0].strip()
        value = value.strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def _canonical_fuel(value: str | None) -> str | None:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    s = re.sub(r"[^a-z0-9]+", " ", raw.lower()).strip()
    if s in {"gasoline", "petrol", "gas"}:
        return "Gasoline"
    if s in {"diesel"}:
        return "Diesel"
    if s in {"hybrid", "gasoline hybrid", "petrol hybrid", "gasoline/hybrid", "petrol/hybrid"}:
        return "Gasoline/hybrid"
    if s in {"plugin hybrid", "plug in hybrid", "plug-in hybrid", "phev"}:
        return "Plugin Hybrid"
    if s in {"electric", "ev", "bev"}:
        return "Electric"
    return raw


def _canonical_transmission(value: str | None) -> str | None:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    s = re.sub(r"[^a-z0-9]+", " ", raw.lower()).strip()
    if s in {"automatic", "auto", "at"}:
        return "Automatic"
    if s in {"manual", "mt"}:
        return "Manual"
    if s in {"cvt"}:
        return "CVT"
    return raw


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize vehicles.fuel_type/transmission values")
    parser.add_argument("--mode", choices=["local", "supabase"], required=True)
    parser.add_argument("--database-url", help="Optional DB URL override")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Preview updates only (default)")
    mode.add_argument("--apply", action="store_true", help="Apply updates")
    args = parser.parse_args()

    mode_env = ROOT / (".env.localdb" if args.mode == "local" else ".env.supabase")
    fallback_env = ROOT / ".env"
    _load_env_file(mode_env)
    _load_env_file(fallback_env)

    db_url = args.database_url or os.getenv("DATABASE_URL")
    if not db_url:
        raise SystemExit("DATABASE_URL is missing for selected mode")

    apply_updates = bool(args.apply)

    engine = create_engine(db_url)
    scanned = 0
    fuel_updates = 0
    transmission_updates = 0

    with engine.begin() as conn:
        rows = conn.execute(text("SELECT id, fuel_type, transmission FROM vehicles")).mappings().all()
        scanned = len(rows)

        for row in rows:
            vehicle_id = row["id"]
            current_fuel = row["fuel_type"]
            current_transmission = row["transmission"]

            next_fuel = _canonical_fuel(current_fuel)
            next_transmission = _canonical_transmission(current_transmission)

            fuel_changed = next_fuel != current_fuel
            transmission_changed = next_transmission != current_transmission

            if fuel_changed:
                fuel_updates += 1
            if transmission_changed:
                transmission_updates += 1

            if apply_updates and (fuel_changed or transmission_changed):
                conn.execute(
                    text(
                        """
                        UPDATE vehicles
                        SET fuel_type = :fuel_type,
                            transmission = :transmission
                        WHERE id = :id
                        """
                    ),
                    {
                        "id": str(vehicle_id),
                        "fuel_type": next_fuel,
                        "transmission": next_transmission,
                    },
                )

    mode_text = "APPLY" if apply_updates else "DRY-RUN"
    print(f"mode={mode_text}")
    print(f"scanned={scanned}")
    print(f"fuel_updates={fuel_updates}")
    print(f"transmission_updates={transmission_updates}")
    if not apply_updates:
        print("No DB changes were written. Re-run with --apply to commit updates.")


if __name__ == "__main__":
    main()
