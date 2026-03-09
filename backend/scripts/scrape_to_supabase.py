"""
Run one-shot live scrape and upload images directly to Supabase Storage.

This script loads backend/.env.supabase first, then falls back to backend/.env.
Usage:
    python scripts/scrape_to_supabase.py
    python scripts/scrape_to_supabase.py --count 80 --years 3
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
    try:
        import supabase  # noqa: F401
    except Exception as exc:
        raise SystemExit(
            "Missing 'supabase' package. Install backend requirements first: "
            "pip install -r requirements.txt"
        ) from exc

    parser = argparse.ArgumentParser(description="Scrape vehicles and upload images directly to Supabase")
    parser.add_argument("--count", type=int, default=50, help="Number of listings to scrape")
    parser.add_argument("--years", type=int, default=3, help="Keep only last N years")
    args = parser.parse_args()

    _load_env_file(ROOT / ".env.supabase")
    _load_env_file(ROOT / ".env")

    os.environ.setdefault("CD23_SCRAPER_MODE", "live")
    os.environ["CD23_SCRAPE_COUNT"] = str(max(1, args.count))
    os.environ["CD23_KEEP_LAST_YEARS"] = str(max(1, args.years))
    os.environ["CD23_UPLOAD_IMAGES_SUPABASE"] = "true"
    os.environ["CD23_REQUIRE_SUPABASE_UPLOAD"] = "true"
    os.environ["CD23_STORE_IMAGES_LOCAL"] = "false"
    os.environ["CD23_FUEL_ENUM_STYLE"] = "upper"
    os.environ["CD23_TRANSMISSION_ENUM_STYLE"] = "upper"

    from app.services.scraper.scheduler import scraper_scheduler

    result = scraper_scheduler.run_now()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
