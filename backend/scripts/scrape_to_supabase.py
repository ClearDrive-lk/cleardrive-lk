"""
Run one-shot live scrape and upload images directly to Supabase Storage.

This script relies on backend/.env via app settings/storage fallbacks.
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

sys.path.append(str(Path(__file__).parent.parent))

from app.services.scraper.scheduler import scraper_scheduler


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

    os.environ.setdefault("CD23_SCRAPER_MODE", "live")
    os.environ["CD23_SCRAPE_COUNT"] = str(max(1, args.count))
    os.environ["CD23_KEEP_LAST_YEARS"] = str(max(1, args.years))
    os.environ["CD23_UPLOAD_IMAGES_SUPABASE"] = "true"
    os.environ["CD23_REQUIRE_SUPABASE_UPLOAD"] = "true"
    os.environ["CD23_STORE_IMAGES_LOCAL"] = "false"

    result = scraper_scheduler.run_now()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
