"""
Single entrypoint for scraping with explicit runtime mode.

Usage:
  python scripts/scrape_runner.py --mode local --count 100 --years 3
  python scripts/scrape_runner.py --mode supabase --count 50 --years 3

By default this script loads:
  - local mode:     backend/.env.localdb
  - supabase mode:  backend/.env.supabase
If those files don't exist, it falls back to backend/.env.
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
        # Strip inline comments for unquoted values: FOO=true  # comment
        if value and not (value.startswith("'") or value.startswith('"')):
            value = value.split("#", 1)[0].strip()
        value = value.strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def main() -> None:
    parser = argparse.ArgumentParser(description="Run vehicle scraping in local or supabase mode")
    parser.add_argument("--mode", choices=["local", "supabase"], required=True)
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Number of listings to scrape. In local mode, defaults to 100; use 0 for all pages.",
    )
    parser.add_argument("--years", type=int, default=3)
    args = parser.parse_args()

    # Load env profile before importing app settings.
    mode_env = ROOT / (".env.localdb" if args.mode == "local" else ".env.supabase")
    fallback_env = ROOT / ".env"
    _load_env_file(mode_env)
    _load_env_file(fallback_env)

    os.environ.setdefault("CD23_SCRAPER_MODE", "live")
    default_count = 100 if args.mode == "local" else 50
    scrape_count = default_count if args.count is None else max(0, args.count)
    os.environ["CD23_SCRAPE_COUNT"] = str(scrape_count)
    os.environ["CD23_KEEP_LAST_YEARS"] = str(max(1, args.years))

    if args.mode == "supabase":
        os.environ["CD23_UPLOAD_IMAGES_SUPABASE"] = "true"
        os.environ["CD23_REQUIRE_SUPABASE_UPLOAD"] = "true"
        os.environ["CD23_STORE_IMAGES_LOCAL"] = "false"
        os.environ["CD23_FUEL_ENUM_STYLE"] = "upper"
        os.environ["CD23_TRANSMISSION_ENUM_STYLE"] = "upper"
    else:
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
