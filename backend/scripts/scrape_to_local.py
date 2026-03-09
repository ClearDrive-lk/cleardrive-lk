"""
Run one-shot live scrape and import directly into the local database.

This script loads backend/.env.localdb first, then falls back to backend/.env.
Usage:
    python scripts/scrape_to_local.py
    python scripts/scrape_to_local.py --count 100 --years 3
    python scripts/scrape_to_local.py --count 0 --years 3
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape vehicles and import directly into the local database")
    parser.add_argument(
        "--count",
        type=int,
        default=100,
        help="Number of listings to scrape. Use 0 to import all available pages.",
    )
    parser.add_argument("--years", type=int, default=3, help="Keep only last N years")
    args = parser.parse_args()

    _load_env_file(ROOT / ".env.localdb")
    _load_env_file(ROOT / ".env")

    os.environ.setdefault("CD23_SCRAPER_MODE", "live")
    os.environ["CD23_SCRAPE_COUNT"] = str(max(0, args.count))
    os.environ["CD23_KEEP_LAST_YEARS"] = str(max(1, args.years))
    os.environ["CD23_UPLOAD_IMAGES_SUPABASE"] = "false"
    os.environ["CD23_REQUIRE_SUPABASE_UPLOAD"] = "false"
    os.environ["CD23_STORE_IMAGES_LOCAL"] = "true"
    os.environ["CD23_FUEL_ENUM_STYLE"] = "title"
    os.environ["CD23_TRANSMISSION_ENUM_STYLE"] = "title"

    from app.services.scraper.scheduler import scraper_scheduler

    result = scraper_scheduler.run_now()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
