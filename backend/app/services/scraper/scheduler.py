"""
CD-23 scraper scheduler with duplicate prevention.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import threading
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlparse

from app.core.cache import cache
from app.core.database import SessionLocal
from app.core.storage import storage
from app.modules.orders.models import Order
from app.modules.vehicles.models import (
    Drive,
    FuelType,
    Transmission,
    Vehicle,
    VehicleStatus,
    VehicleType,
)
from app.services.scraper.auction_scraper import AuctionSiteScraper
from app.services.scraper.mock_scraper import MockVehicleScraper
from requests import RequestException  # type: ignore[import-untyped]
from requests import Session as RequestsSession  # type: ignore[import-untyped]
from sqlalchemy import exists
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _vehicle_bucket_name() -> str:
    return os.getenv("SUPABASE_STORAGE_VEHICLE_BUCKET", "Photos").strip() or "Photos"


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _run_async(coro: Any) -> Any:
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger

    APSCHEDULER_AVAILABLE = True
except Exception:  # pragma: no cover - defensive fallback if dependency missing
    BackgroundScheduler = None  # type: ignore[assignment]
    CronTrigger = None  # type: ignore[assignment]
    APSCHEDULER_AVAILABLE = False


def _map_fuel(value: str | None) -> str | None:
    if not value:
        return None
    s = value.strip().lower()
    enum_style = os.getenv("CD23_FUEL_ENUM_STYLE", "title").strip().lower()
    upper = enum_style == "upper"
    if s in {"petrol", "gasoline"}:
        return "PETROL" if upper else FuelType.GASOLINE.value
    if s in {"hybrid", "petrol/hybrid", "gasoline/hybrid"}:
        return "HYBRID" if upper else FuelType.HYBRID.value
    if s in {"plugin hybrid", "plug-in hybrid"}:
        return "PLUGIN_HYBRID" if upper else FuelType.PLUGIN_HYBRID.value
    if s == "diesel":
        return "DIESEL" if upper else FuelType.DIESEL.value
    if s == "electric":
        return "ELECTRIC" if upper else FuelType.ELECTRIC.value
    return None


def _map_transmission(value: str | None) -> str | None:
    if not value:
        return None
    s = value.strip().lower()
    enum_style = os.getenv("CD23_TRANSMISSION_ENUM_STYLE", "title").strip().lower()
    upper = enum_style == "upper"
    if s == "automatic":
        return "AUTOMATIC" if upper else Transmission.AUTOMATIC.value
    if s == "manual":
        return "MANUAL" if upper else Transmission.MANUAL.value
    if s == "cvt":
        return "CVT" if upper else Transmission.CVT.value
    return None


def _map_vehicle_type(value: str | None) -> str | None:
    if not value:
        return None
    s = value.strip().lower()
    mapping = {
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
    return mapping.get(s)


def _map_drive(value: str | None) -> str | None:
    if not value:
        return None
    s = value.strip().upper()
    if s == "2WD":
        return Drive.TWO_WD.value
    if s == "4WD":
        return Drive.FOUR_WD.value
    if s == "AWD":
        return Drive.AWD.value
    if s == "FWD":
        return Drive.TWO_WD.value
    return None


def _map_steering(value: str | None) -> str | None:
    if not value:
        return None
    s = value.strip().lower()
    if s in {"right hand", "right", "rhd"}:
        return "RIGHT_HAND"
    if s in {"left hand", "left", "lhd"}:
        return "LEFT_HAND"
    return None


def _normalize_row_enums(row: dict[str, Any]) -> None:
    fuel_value = _map_fuel(row.get("fuel_type"))
    if fuel_value is not None:
        row["fuel_type"] = fuel_value

    row["transmission"] = _map_transmission(row.get("transmission"))

    row["vehicle_type"] = _map_vehicle_type(row.get("vehicle_type") or row.get("body_type"))
    row["drive"] = _map_drive(row.get("drive") or row.get("drive_type"))
    row["steering"] = _map_steering(row.get("steering"))


class ScraperScheduler:
    def __init__(self) -> None:
        self.scheduler = (
            BackgroundScheduler(timezone="Asia/Colombo") if APSCHEDULER_AVAILABLE else None
        )
        self.is_running = False
        self._job_lock = threading.Lock()
        self._live_scraper = AuctionSiteScraper()
        self._scraper = MockVehicleScraper()
        self._http = RequestsSession()
        self._http.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
                ),
                "Referer": "https://www.ramadbk.com/search_by_usual.php?stock_country=1",
            }
        )

    def _find_existing_vehicle(self, db: Session, vehicle_data: dict[str, Any]) -> Vehicle | None:
        stock_no = vehicle_data.get("stock_no")
        if stock_no:
            existing = db.query(Vehicle).filter(Vehicle.stock_no == str(stock_no)).first()
            if existing:
                return existing

        chassis = vehicle_data.get("chassis") or vehicle_data.get("chassis_number")
        if self._is_meaningful_identity_value(chassis):
            existing = db.query(Vehicle).filter(Vehicle.chassis == chassis).first()
            if existing:
                return existing

        vehicle_url = vehicle_data.get("vehicle_url")
        if self._is_meaningful_identity_value(vehicle_url):
            existing = db.query(Vehicle).filter(Vehicle.vehicle_url == str(vehicle_url)).first()
            if existing:
                return existing
        return None

    @staticmethod
    def _is_meaningful_identity_value(value: Any) -> bool:
        text = str(value or "").strip()
        if not text:
            return False
        normalized = text.lower()
        if normalized in {"****", "***", "**", "*", "-", "--", "n/a", "na", "unknown"}:
            return False
        return any(char.isalnum() for char in text)

    @staticmethod
    def _should_import_row(row: dict[str, Any]) -> bool:
        price = row.get("price_jpy")
        try:
            if price is None or Decimal(str(price)) <= 0:
                return False
        except Exception:
            return False
        status = str(row.get("status") or VehicleStatus.AVAILABLE.value).upper()
        return status == VehicleStatus.AVAILABLE.value

    def _should_update_vehicle(
        self, existing: Vehicle, new_data: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        changed_fields: list[str] = []

        new_price = new_data.get("price_jpy")
        if new_price is not None and existing.price_jpy:
            old_price = Decimal(str(existing.price_jpy))
            incoming_price = Decimal(str(new_price))
            if old_price > 0:
                price_change_pct = (abs(incoming_price - old_price) / old_price) * Decimal("100")
                if price_change_pct >= Decimal("5"):
                    changed_fields.append("price_jpy")

        new_status = new_data.get("status")
        if new_status and new_status != existing.status.value:
            changed_fields.append("status")

        new_mileage = new_data.get("mileage_km")
        if new_mileage is not None and existing.mileage_km is not None:
            mileage_diff = abs(int(new_mileage) - int(existing.mileage_km))
            if mileage_diff >= 1000:
                changed_fields.append("mileage_km")

        new_image_url = new_data.get("image_url")
        if new_image_url and new_image_url != existing.image_url:
            changed_fields.append("image_url")

        enrich_fields = [
            "make",
            "model",
            "year",
            "stock_no",
            "chassis",
            "reg_year",
            "vehicle_type",
            "body_type",
            "grade",
            "engine_cc",
            "fuel_type",
            "transmission",
            "steering",
            "drive",
            "seats",
            "doors",
            "color",
            "location",
            "options",
            "other_remarks",
            "gallery_images",
            "vehicle_url",
        ]
        for field in enrich_fields:
            incoming = new_data.get(field)
            if incoming is None or incoming == "":
                continue
            current = getattr(existing, field, None)
            if current is None or str(current).strip() != str(incoming).strip():
                changed_fields.append(field)

        return len(changed_fields) > 0, changed_fields

    def _apply_updates(
        self, existing: Vehicle, new_data: dict[str, Any], changed_fields: list[str]
    ) -> None:
        for field in changed_fields:
            if field == "price_jpy":
                setattr(existing, field, Decimal(str(new_data[field])))
            elif field == "year":
                setattr(existing, field, _to_int(new_data[field]))
            elif field == "status":
                setattr(existing, field, VehicleStatus(new_data[field]))
            elif field == "mileage_km":
                setattr(existing, field, int(new_data[field]))
            else:
                setattr(existing, field, new_data[field])
        setattr(existing, "updated_at", datetime.utcnow())

    def _vehicle_from_scraped(self, row: dict[str, Any]) -> Vehicle:
        images = row.get("images") or []
        primary_image = row.get("image_url") or (images[0] if images else None)
        status_value = row.get("status") or VehicleStatus.AVAILABLE.value
        try:
            status = VehicleStatus(status_value)
        except Exception:
            status = VehicleStatus.AVAILABLE

        return Vehicle(
            stock_no=row.get("stock_no") or f"SCR-{int(datetime.utcnow().timestamp() * 1000)}",
            chassis=row.get("chassis") or row.get("chassis_number"),
            make=row.get("make"),
            model=row.get("model"),
            reg_year=row.get("reg_year"),
            year=_to_int(row.get("year")) or datetime.utcnow().year,
            vehicle_type=_map_vehicle_type(row.get("vehicle_type") or row.get("body_type")),
            body_type=row.get("body_type"),
            grade=row.get("grade") or row.get("auction_grade"),
            price_jpy=Decimal(str(row.get("price_jpy"))),
            mileage_km=row.get("mileage_km"),
            engine_cc=row.get("engine_cc"),
            engine_model=row.get("engine_model"),
            fuel_type=_map_fuel(row.get("fuel_type")),
            transmission=_map_transmission(row.get("transmission")),
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
            other_remarks=row.get("other_remarks") or row.get("description"),
            image_url=primary_image,
            gallery_images=json.dumps(images) if isinstance(images, list) and images else None,
            vehicle_url=row.get("vehicle_url"),
            model_no=row.get("model_no"),
            status=status.value,
        )

    def _load_fallback_dataset(self) -> list[dict[str, Any]]:
        data_root = Path(__file__).resolve().parents[3] / "data"
        candidates = (data_root / "static_vehicles.json", data_root / "vehicles.json")

        for data_path in candidates:
            if not data_path.exists():
                continue
            with data_path.open("r", encoding="utf-8") as fp:
                payload = json.load(fp)
            if isinstance(payload, dict):
                vehicles = payload.get("vehicles", [])
            elif isinstance(payload, list):
                vehicles = payload
            else:
                vehicles = []

            logger.info("Loaded fallback dataset from %s (%s rows)", data_path, len(vehicles))
            return cast(list[dict[str, Any]], vehicles)

        logger.warning("No fallback dataset found in %s", data_root)
        return []

    def _scrape_vehicle_rows(self, count: int = 10) -> list[dict[str, Any]]:
        mode = os.getenv("CD23_SCRAPER_MODE", "hybrid").strip().lower()

        if mode == "mock":
            return self._scraper.scrape(count=count)

        if mode == "live":
            return self._live_scraper.scrape(count=count)

        live_rows = self._live_scraper.scrape(count=count)
        if live_rows:
            return live_rows

        logger.warning("Live scraper returned no rows, switching to mock scraper")
        return self._scraper.scrape(count=count)

    @staticmethod
    def _resolve_scrape_count() -> int:
        raw_value = os.getenv("CD23_SCRAPE_COUNT", "10").strip().lower()
        if raw_value in {"all", "full", "unlimited"}:
            return 0
        try:
            return int(raw_value)
        except ValueError:
            logger.warning("Invalid CD23_SCRAPE_COUNT=%r, defaulting to 10", raw_value)
            return 10

    @staticmethod
    def _year_cutoff() -> int | None:
        keep_years_raw = os.getenv("CD23_KEEP_LAST_YEARS", "3").strip()
        try:
            keep_years = int(keep_years_raw)
        except ValueError:
            keep_years = 3
        if keep_years <= 0:
            return None
        return datetime.utcnow().year - keep_years + 1

    @staticmethod
    def _safe_slug(value: str) -> str:
        compact = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
        return compact[:80] or "vehicle"

    def _download_and_store_images(self, row: dict[str, Any]) -> list[str]:
        upload_supabase = os.getenv("CD23_UPLOAD_IMAGES_SUPABASE", "false").strip().lower() not in {
            "0",
            "false",
            "no",
        }
        require_supabase_upload = os.getenv(
            "CD23_REQUIRE_SUPABASE_UPLOAD", "false"
        ).strip().lower() not in {
            "0",
            "false",
            "no",
        }
        store_local = os.getenv("CD23_STORE_IMAGES_LOCAL", "true").strip().lower() not in {
            "0",
            "false",
            "no",
        }
        sources: list[str] = []
        image_url = row.get("image_url")
        if isinstance(image_url, str) and image_url:
            sources.append(image_url)
        images = row.get("images")
        if isinstance(images, list):
            sources.extend([str(item) for item in images if item])

        unique_sources = []
        seen: set[str] = set()
        for src in sources:
            if src not in seen and src.startswith(("http://", "https://")):
                seen.add(src)
                unique_sources.append(src)

        if not unique_sources:
            return []

        if upload_supabase:
            stock_no = str(row.get("stock_no") or "")
            default_slug = (
                f"{row.get('make', '')}-{row.get('model', '')}-{row.get('year', '')}".strip("-")
            )
            slug = self._safe_slug(stock_no or default_slug or "vehicle")
            uploaded_urls: list[str] = []
            for idx, src in enumerate(unique_sources[:10], start=1):
                try:
                    response = self._http.get(src, timeout=12)
                    response.raise_for_status()
                except RequestException as exc:
                    logger.warning("Image download failed for %s: %s", src, exc)
                    continue

                content_type = response.headers.get("Content-Type", "").lower()
                if content_type and not content_type.startswith("image/"):
                    logger.warning("Skipping non-image URL %s (content-type=%s)", src, content_type)
                    continue

                suffix = Path(urlparse(src).path).suffix.lower()
                if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
                    suffix = ".jpg"
                file_path = f"{slug}/image_{idx}{suffix}"
                try:
                    result = _run_async(
                        storage.upload_file(
                            bucket=_vehicle_bucket_name(),
                            file_path=file_path,
                            file_content=response.content,
                            content_type=content_type or "application/octet-stream",
                        )
                    )
                    public_url = result.get("url")
                    if public_url:
                        uploaded_urls.append(str(public_url))
                except Exception as exc:
                    message = str(exc).lower()
                    if (
                        "duplicate" in message
                        or "already exists" in message
                        or "statuscode': 409" in message
                    ):
                        try:
                            public_url = _run_async(
                                storage.get_public_url(_vehicle_bucket_name(), file_path)
                            )
                            if public_url:
                                uploaded_urls.append(str(public_url))
                                continue
                        except Exception:
                            pass
                    logger.warning("Supabase upload failed for %s: %s", file_path, exc)

            if uploaded_urls:
                return uploaded_urls
            if require_supabase_upload:
                raise RuntimeError("Supabase upload required but no images were uploaded")
            # Fallback to remote URLs if upload mode is on but upload failed.
            return unique_sources[:3]

        if not store_local:
            return unique_sources[:3]

        stock_no = str(row.get("stock_no") or "")
        default_slug = f"{row.get('make', '')}-{row.get('model', '')}-{row.get('year', '')}".strip(
            "-"
        )
        slug = self._safe_slug(stock_no or default_slug or "vehicle")

        images_root = Path(__file__).resolve().parents[3] / "data" / "vehicle_images" / slug
        images_root.mkdir(parents=True, exist_ok=True)

        local_paths: list[str] = []
        for idx, src in enumerate(unique_sources[:3], start=1):
            try:
                response = self._http.get(src, timeout=12)
                response.raise_for_status()
            except RequestException as exc:
                logger.warning("Image download failed for %s: %s", src, exc)
                continue

            content_type = response.headers.get("Content-Type", "").lower()
            if content_type and not content_type.startswith("image/"):
                logger.warning("Skipping non-image URL %s (content-type=%s)", src, content_type)
                continue

            suffix = Path(urlparse(src).path).suffix.lower()
            if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
                suffix = ".jpg"

            local_file_path = images_root / f"image_{idx}{suffix}"
            local_file_path.write_bytes(response.content)
            local_paths.append(
                str(local_file_path.relative_to(Path(__file__).resolve().parents[3]))
            )

        return local_paths

    def scrape_and_import(self) -> dict[str, int]:
        stats = {"scraped": 0, "new": 0, "updated": 0, "skipped": 0, "removed": 0, "errors": 0}
        scrape_count = self._resolve_scrape_count()
        year_cutoff = self._year_cutoff()

        if not self._job_lock.acquire(blocking=False):
            logger.info("Scraper job skipped because a run is already in progress")
            return stats

        db = SessionLocal()
        try:
            try:
                vehicles_data = self._scrape_vehicle_rows(count=scrape_count)
            except Exception as exc:
                logger.exception("Scraping failed, falling back to static dataset: %s", exc)
                vehicles_data = self._load_fallback_dataset()

            stats["scraped"] = len(vehicles_data)
            logger.info("CD-23 scrape started: records=%s", stats["scraped"])

            for row in vehicles_data:
                try:
                    # Keep catalog bounded to the most recent N years.
                    if year_cutoff is not None:
                        row_year = _to_int(row.get("year"))
                        if row_year is None or row_year < year_cutoff:
                            stats["skipped"] += 1
                            continue

                    # Normalize scraper values before both update/insert paths.
                    _normalize_row_enums(row)
                    if not self._should_import_row(row):
                        stats["skipped"] += 1
                        continue

                    downloaded_images = self._download_and_store_images(row)
                    if downloaded_images:
                        row["images"] = downloaded_images
                        row["image_url"] = downloaded_images[0]
                        row["gallery_images"] = json.dumps(downloaded_images)
                    else:
                        raw_images = row.get("images")
                        if isinstance(raw_images, list) and raw_images:
                            row["gallery_images"] = json.dumps(raw_images)

                    existing = self._find_existing_vehicle(db, row)
                    if existing:
                        should_update, changed_fields = self._should_update_vehicle(existing, row)
                        if should_update:
                            self._apply_updates(existing, row, changed_fields)
                            stats["updated"] += 1
                        else:
                            stats["skipped"] += 1
                        continue

                    vehicle = self._vehicle_from_scraped(row)
                    db.add(vehicle)
                    stats["new"] += 1
                except Exception as exc:
                    stats["errors"] += 1
                    logger.exception("Error processing scraped vehicle row: %s", exc)

            if year_cutoff is not None:
                removed_count = (
                    db.query(Vehicle)
                    .filter(Vehicle.year < year_cutoff)
                    .filter(~exists().where(Order.vehicle_id == Vehicle.id))
                    .delete(synchronize_session=False)
                )
                stats["removed"] = int(removed_count or 0)

            unwanted_scraped_rows = (
                db.query(Vehicle)
                .filter(Vehicle.vehicle_url.ilike("%ramadbk.com%"))
                .filter(~exists().where(Order.vehicle_id == Vehicle.id))
                .filter(
                    (Vehicle.price_jpy <= 0) | (Vehicle.status != VehicleStatus.AVAILABLE.value)
                )
                .delete(synchronize_session=False)
            )
            stats["removed"] += int(unwanted_scraped_rows or 0)

            db.commit()
            try:
                _run_async(cache.clear_pattern("vehicles:*"))
            except Exception as exc:
                logger.warning("Failed to clear vehicle cache after scrape: %s", exc)
            logger.info("CD-23 scrape completed: %s", stats)
            return stats
        except Exception:
            db.rollback()
            stats["errors"] += 1
            logger.exception("CD-23 scrape import failed")
            return stats
        finally:
            db.close()
            self._job_lock.release()

    def start(self) -> None:
        if not APSCHEDULER_AVAILABLE:
            logger.warning("APScheduler not installed. CD-23 scheduler disabled.")
            return
        if self.is_running or self.scheduler is None:
            return
        self.scheduler.add_job(
            func=self.scrape_and_import,
            trigger=CronTrigger(hour=2, minute=0),
            id="daily_vehicle_scrape",
            name="Daily Vehicle Scrape",
            replace_existing=True,
        )
        self.scheduler.start()
        self.is_running = True
        logger.info(
            "CD-23 scheduler started: daily at 02:00 (next=%s)",
            self.scheduler.get_job("daily_vehicle_scrape").next_run_time,
        )

    def stop(self) -> None:
        if self.scheduler is not None and self.scheduler.running:
            self.scheduler.shutdown(wait=False)
        self.is_running = False

    def run_now(self) -> dict[str, int]:
        return self.scrape_and_import()


scraper_scheduler = ScraperScheduler()
