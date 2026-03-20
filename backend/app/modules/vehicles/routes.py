# backend/app/modules/vehicles/routes.py

import json
import math
import re
import threading
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from urllib.parse import urljoin
from uuid import UUID

import requests  # type: ignore[import-untyped]
from app.core.cache import cache
from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.models.gazette import TaxFuelType, TaxVehicleType
from app.modules.vehicles.models import Vehicle, VehicleStatus, VehicleType
from app.modules.vehicles.schemas import (
    CostBreakdown,
    PaginationInfo,
    VehicleCreate,
    VehicleListResponse,
    VehicleResponse,
    VehicleUpdate,
)
from app.services.tax_calculator import (
    InsufficientVehicleDataError,
    NoTaxRuleError,
    calculate_tax,
)
from app.services.catalog_tax_calculator import calculate_catalog_tax
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import asc, case, desc, or_, text
from sqlalchemy.orm import Session

try:
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover - optional dependency
    BeautifulSoup = None  # type: ignore[assignment]

from .cost_calculator import (
    DEFAULT_JPY_TO_LKR,
    calculate_clearance_fee,
    calculate_documentation_fee,
    calculate_port_charges,
    calculate_shipping_cost,
)

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])

FX_PROVIDER = "frankfurter"
FX_ENDPOINT = "https://api.frankfurter.dev/v1/latest"
FX_CACHE_TTL_SECONDS = 6 * 60 * 60


def _canonical_fuel_key(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", value.strip().lower()).strip()
    if normalized in {"gasoline", "petrol", "gas"}:
        return "petrol"
    if normalized in {"diesel"}:
        return "diesel"
    if normalized in {
        "hybrid",
        "gasoline hybrid",
        "petrol hybrid",
        "gasoline/hybrid",
        "petrol/hybrid",
    }:
        return "hybrid"
    if normalized in {"plugin hybrid", "plug in hybrid", "plug-in hybrid", "phev"}:
        return "plugin_hybrid"
    if normalized in {"electric", "ev", "bev"}:
        return "electric"
    if normalized in {"cng"}:
        return "cng"
    return normalized


def _resolve_fuel_enum_label(db: Session, requested: str) -> str | None:
    if not db.bind or db.bind.dialect.name != "postgresql":
        return requested
    rows = db.execute(text("""
            SELECT e.enumlabel
            FROM pg_enum e
            JOIN pg_type t ON e.enumtypid = t.oid
            WHERE t.typname = 'fueltype'
            """)).fetchall()
    labels = [str(r[0]) for r in rows]
    if not labels:
        return requested

    by_key: dict[str, list[str]] = {}
    for label in labels:
        key = _canonical_fuel_key(label)
        by_key.setdefault(key, []).append(label)

    req_key = _canonical_fuel_key(requested)
    candidates = by_key.get(req_key, [])
    if not candidates:
        return None

    # Deterministic preference for common variants.
    preferred = [
        "PETROL",
        "DIESEL",
        "HYBRID",
        "ELECTRIC",
        "CNG",
        "PLUGIN_HYBRID",
        "Gasoline",
        "Diesel",
        "Gasoline/hybrid",
        "Electric",
        "Plugin Hybrid",
    ]
    for value in preferred:
        if value in candidates:
            return value
    return candidates[0]


def _fuel_filter_values(requested: str) -> list[str]:
    key = _canonical_fuel_key(requested)
    mapping = {
        "petrol": ["Gasoline", "Petrol", "PETROL"],
        "gasoline": ["Gasoline", "Petrol", "PETROL"],
        "hybrid": [
            "Gasoline/hybrid",
            "Gasoline/Hybrid",
            "HYBRID",
            "Plugin Hybrid",
            "Plug-in Hybrid",
            "PLUGIN_HYBRID",
            "%Hybrid%",
        ],
        "plugin_hybrid": ["Plugin Hybrid", "Plug-in Hybrid", "PLUGIN_HYBRID", "%Plugin%Hybrid%"],
        "diesel": ["Diesel", "DIESEL"],
        "electric": ["Electric", "ELECTRIC", "%Electric%"],
        "cng": ["CNG"],
    }
    return mapping.get(key, [requested])


def _canonical_transmission_key(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", value.strip().lower()).strip()
    if normalized in {"automatic", "auto", "at"}:
        return "automatic"
    if normalized in {"manual", "mt"}:
        return "manual"
    if normalized in {"cvt"}:
        return "cvt"
    return normalized


def _canonical_vehicle_type_key(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", value.strip().lower()).strip()
    if normalized in {"suv", "suvs", "sport utility vehicle", "sport utility"}:
        return "suv"
    if normalized in {"sedan", "saloon"}:
        return "sedan"
    if normalized in {"hatchback", "hatch"}:
        return "hatchback"
    if normalized in {"van", "minivan", "mini van", "van minivan", "mpv"}:
        return "van_minivan"
    if normalized in {"wagon"}:
        return "wagon"
    if normalized in {"pickup", "pick up", "pickup truck"}:
        return "pickup"
    if normalized in {"coupe"}:
        return "coupe"
    if normalized in {"convertible", "cabriolet"}:
        return "convertible"
    if normalized in {"bikes", "bike", "motorcycle", "motorbike"}:
        return "bikes"
    if normalized in {"machinery", "heavy machinery", "equipment"}:
        return "machinery"
    return normalized


def _resolve_vehicle_type_enum(requested: str) -> VehicleType | None:
    key = _canonical_vehicle_type_key(requested)
    mapping = {
        "sedan": VehicleType.SEDAN,
        "suv": VehicleType.SUV,
        "hatchback": VehicleType.HATCHBACK,
        "van_minivan": VehicleType.VAN_MINIVAN,
        "wagon": VehicleType.WAGON,
        "pickup": VehicleType.PICKUP,
        "coupe": VehicleType.COUPE,
        "convertible": VehicleType.CONVERTIBLE,
        "bikes": VehicleType.BIKES,
        "machinery": VehicleType.MACHINERY,
    }
    return mapping.get(key)


def _vehicle_type_filter_values(requested: str) -> list[str]:
    key = _canonical_vehicle_type_key(requested)
    mapping = {
        "suv": ["SUV", "SUVs"],
        "sedan": ["Sedan", "Saloon"],
        "hatchback": ["Hatchback", "Hatch"],
        "van_minivan": ["Van/minivan", "Van", "Minivan", "MPV"],
        "wagon": ["Wagon", "Estate"],
        "pickup": ["Pickup", "Pick up", "Pickup Truck", "Truck"],
        "coupe": ["Coupe"],
        "convertible": ["Convertible", "Cabriolet"],
        "bikes": ["Bikes", "Bike", "Motorcycle", "Motorbike"],
        "machinery": ["Machinery", "Heavy Machinery", "Equipment"],
    }
    return mapping.get(key, [requested])


def _resolve_transmission_enum_label(db: Session, requested: str) -> str | None:
    if not db.bind or db.bind.dialect.name != "postgresql":
        return requested
    rows = db.execute(text("""
            SELECT e.enumlabel
            FROM pg_enum e
            JOIN pg_type t ON e.enumtypid = t.oid
            WHERE t.typname = 'transmission'
            """)).fetchall()
    labels = [str(r[0]) for r in rows]
    if not labels:
        return requested

    by_key: dict[str, list[str]] = {}
    for label in labels:
        key = _canonical_transmission_key(label)
        by_key.setdefault(key, []).append(label)

    req_key = _canonical_transmission_key(requested)
    candidates = by_key.get(req_key, [])
    if not candidates:
        return None

    preferred = ["AUTOMATIC", "MANUAL", "CVT", "Automatic", "Manual", "Cvt"]
    for value in preferred:
        if value in candidates:
            return value
    return candidates[0]


def _transmission_filter_values(requested: str) -> list[str]:
    key = _canonical_transmission_key(requested)
    mapping = {
        "automatic": ["Automatic", "AUTOMATIC", "AT", "A/T", "Auto"],
        "manual": ["Manual", "MANUAL", "MT", "M/T"],
        "cvt": ["CVT", "Cvt"],
    }
    return mapping.get(key, [requested])


def _scrape_vehicle_gallery_images(vehicle_url: str) -> list[str]:
    if not vehicle_url:
        return []
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.ramadbk.com/search_by_usual.php?stock_country=1",
    }
    try:
        response = requests.get(vehicle_url, timeout=20, headers=headers)
        response.raise_for_status()
    except Exception:
        return []

    html = response.text
    images: list[str] = []
    seen: set[str] = set()

    def to_hq(url: str) -> str:
        full = urljoin(vehicle_url, url.strip())
        lower = full.lower()
        if "/vimgs/thumb/" in lower:
            full = full.replace("/VIMGS/thumb/", "/VIMGS/images/").replace(
                "/vimgs/thumb/", "/VIMGS/images/"
            )
            filename = full.rsplit("/", 1)[-1]
            if filename.startswith("T"):
                full = full.rsplit("/", 1)[0] + "/" + filename[1:]
        elif "/vimgs/medium/" in lower:
            full = full.replace("/VIMGS/medium/", "/VIMGS/images/").replace(
                "/vimgs/medium/", "/VIMGS/images/"
            )
        return full

    def dedupe_key(full: str) -> str:
        filename = full.rsplit("/", 1)[-1]
        # thumb variants are often prefixed with T (e.g., TAxxxx -> Axxxx)
        if filename.startswith("T"):
            filename = filename[1:]
        return filename.lower()

    def add(url: str | None) -> None:
        if not url:
            return
        full = to_hq(url)
        if not full.startswith(("http://", "https://")):
            return
        lower = full.lower()
        # Keep only vehicle gallery paths; drop site chrome/icons.
        if "/vimgs/images/" not in lower and "/car_images/" not in lower:
            return
        key = dedupe_key(full)
        if key in seen:
            return
        seen.add(key)
        images.append(full)

    # Direct image URLs in RAMADBK markup/script.
    for match in re.findall(r"https?://[^\"'\s>]+/VIMGS/[^\"'\s<]+", html, flags=re.IGNORECASE):
        add(match)

    if BeautifulSoup is None:
        return images[:12]

    soup = BeautifulSoup(html, "lxml")

    for node in soup.select("a[href], img[src], img[data-src]"):
        add(node.get("href"))
        add(node.get("src"))
        add(node.get("data-src"))
        onmouseover = node.get("onmouseover") or ""
        # RAMADBK thumbnail hover often sets large image URL in JS.
        for match in re.findall(
            r"https?://[^\"'\s>]+/VIMGS/[^\"'\s<]+", onmouseover, flags=re.IGNORECASE
        ):
            add(match)

    return images[:40]


def _map_vehicle_type_to_tax(vehicle: Vehicle) -> str:
    """Map vehicle model type to tax rule enum values."""
    value = vehicle.vehicle_type.value.upper() if vehicle.vehicle_type else ""
    if _map_fuel_type_to_tax(vehicle) == TaxFuelType.ELECTRIC.value:
        if value == "PICKUP":
            return TaxVehicleType.TRUCK.value
        return TaxVehicleType.ELECTRIC.value
    mapping = {
        "SEDAN": TaxVehicleType.SEDAN.value,
        "SUV": TaxVehicleType.SUV.value,
        "PICKUP": TaxVehicleType.TRUCK.value,
        "VAN/MINIVAN": TaxVehicleType.VAN.value,
        "WAGON": TaxVehicleType.VAN.value,
        "HATCHBACK": TaxVehicleType.OTHER.value,
        "COUPE": TaxVehicleType.OTHER.value,
        "CONVERTIBLE": TaxVehicleType.OTHER.value,
        "BIKES": TaxVehicleType.MOTORCYCLE.value,
        "MACHINERY": TaxVehicleType.OTHER.value,
    }
    return mapping.get(value, TaxVehicleType.OTHER.value)


def _map_fuel_type_to_tax(vehicle: Vehicle) -> str:
    """Map vehicle fuel enum to tax fuel types."""
    raw = vehicle.fuel_type
    value = str(getattr(raw, "value", raw) or "").upper()
    if "HYBRID" in value:
        return TaxFuelType.HYBRID.value
    if "DIESEL" in value:
        return TaxFuelType.DIESEL.value
    if "ELECTRIC" in value:
        return TaxFuelType.ELECTRIC.value
    if "GASOLINE" in value or "PETROL" in value:
        return TaxFuelType.PETROL.value
    return TaxFuelType.OTHER.value


def _derive_tax_category_codes(vehicle: Vehicle) -> list[str]:
    raw_type = vehicle.vehicle_type.value.upper() if vehicle.vehicle_type else ""
    raw_fuel = str(getattr(vehicle.fuel_type, "value", vehicle.fuel_type) or "").upper()
    categories: list[str] = []

    if "ELECTRIC" in raw_fuel:
        if raw_type == "PICKUP":
            categories.append("GOODS_VEHICLE_ELECTRIC")
        elif raw_type in {"SEDAN", "SUV", "HATCHBACK", "WAGON", "COUPE", "CONVERTIBLE"}:
            categories.extend(["PASSENGER_VEHICLE_BEV", "PASSENGER_VEHICLE_ELECTRIC"])

    return categories


# ============================================================================
# PUBLIC ENDPOINTS (No auth required)
# ============================================================================


@router.get("", response_model=VehicleListResponse)
async def get_vehicles(
    # Search & Filter Parameters
    search: Optional[str] = Query(None, description="Search in make/model"),
    make: Optional[str] = Query(None, description="Filter by manufacturer"),
    model: Optional[str] = Query(None, description="Filter by model"),
    vehicle_type: Optional[str] = Query(None, description="Filter by vehicle type"),
    year_min: Optional[int] = Query(None, ge=1990, description="Minimum year"),
    year_max: Optional[int] = Query(None, le=2026, description="Maximum year"),
    recent_only: bool = Query(
        False,
        description="If true and year_min is not provided, defaults to last 3 years",
    ),
    price_min: Optional[Decimal] = Query(None, ge=0, description="Minimum price (JPY)"),
    price_max: Optional[Decimal] = Query(None, ge=0, description="Maximum price (JPY)"),
    mileage_max: Optional[int] = Query(None, ge=0, description="Maximum mileage (km)"),
    fuel_type: Optional[str] = Query(None, description="Filter by fuel type"),
    transmission: Optional[str] = Query(None, description="Filter by transmission"),
    status: Optional[VehicleStatus] = Query(None, description="Filter by status"),
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    # Sorting
    sort_by: str = Query(
        "created_at",
        pattern="^(price_jpy|year|reg_year|mileage_km|created_at)$",
        description="Field to sort by",
    ),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    # Database session
    db: Session = Depends(get_db),
):
    """
    Get paginated list of vehicles with filters and sorting.

    **Query Parameters:**
    - `search`: Search text for make/model
    - `make`: Filter by manufacturer (e.g., "Toyota")
    - `model`: Filter by model (e.g., "Prius")
    - `vehicle_type`: Filter by vehicle type (e.g., "SUV", "Sedan")
    - `year_min`, `year_max`: Year range filter
    - `recent_only`: Restrict to last 3 years when `year_min` is omitted
    - `price_min`, `price_max`: Price range in JPY
    - `mileage_max`: Maximum mileage filter
    - `fuel_type`: Filter by fuel type
    - `transmission`: Filter by transmission type
    - `status`: Filter by status (default: AVAILABLE)
    - `page`: Page number (default: 1)
    - `limit`: Results per page (default: 20, max: 100)
    - `sort_by`: Field to sort by (price_jpy, year, reg_year, mileage_km, created_at)
    - `sort_order`: Sort order (asc or desc)

    **Returns:**
    - List of vehicles matching filters
    - Pagination information

    Public endpoint - no authentication required.
    """
    cache_key = cache.generate_key(
        "vehicles",
        search=search,
        make=make,
        model=model,
        vehicle_type=vehicle_type,
        year_min=year_min,
        year_max=year_max,
        recent_only=recent_only,
        price_min=price_min,
        price_max=price_max,
        mileage_max=mileage_max,
        fuel_type=fuel_type,
        transmission=transmission,
        status=status.value if status else None,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    cached_response = await cache.get(cache_key)
    if cached_response:
        return VehicleListResponse.model_validate(cached_response)

    # Build query
    query = db.query(Vehicle)

    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Vehicle.stock_no.ilike(search_term),
                Vehicle.chassis.ilike(search_term),
                Vehicle.make.ilike(search_term),
                Vehicle.model.ilike(search_term),
                Vehicle.model_no.ilike(search_term),
                Vehicle.grade.ilike(search_term),
                Vehicle.body_type.ilike(search_term),
                Vehicle.color.ilike(search_term),
                Vehicle.options.ilike(search_term),
                Vehicle.other_remarks.ilike(search_term),
            )
        )

    if make:
        query = query.filter(Vehicle.make.ilike(f"%{make}%"))

    if model:
        query = query.filter(Vehicle.model.ilike(f"%{model}%"))

    if vehicle_type:
        resolved_type = _resolve_vehicle_type_enum(vehicle_type)
        type_candidates = _vehicle_type_filter_values(vehicle_type)
        clauses = []
        if resolved_type is not None:
            clauses.append(Vehicle.vehicle_type == resolved_type)
        for value in type_candidates:
            clauses.append(Vehicle.body_type.ilike(f"%{value}%"))
        query = query.filter(or_(*clauses))

    if recent_only and year_min is None:
        year_min = datetime.utcnow().year - 2

    if year_min:
        query = query.filter(Vehicle.year >= year_min)

    if year_max:
        query = query.filter(Vehicle.year <= year_max)

    if price_min:
        query = query.filter(Vehicle.price_jpy >= price_min)

    if price_max:
        query = query.filter(Vehicle.price_jpy <= price_max)

    if mileage_max:
        query = query.filter(Vehicle.mileage_km <= mileage_max)

    if fuel_type:
        candidates = _fuel_filter_values(fuel_type)
        query = query.filter(or_(*[Vehicle.fuel_type.ilike(val) for val in candidates]))

    if transmission:
        candidates = _transmission_filter_values(transmission)
        query = query.filter(or_(*[Vehicle.transmission.ilike(val) for val in candidates]))

    if status:
        query = query.filter(Vehicle.status == status)

    # Get total count before pagination
    total = query.count()

    # Apply sorting
    sort_column = getattr(Vehicle, sort_by)
    if sort_by == "price_jpy":
        zero_last = case((Vehicle.price_jpy == 0, 1), else_=0)
        if sort_order == "desc":
            query = query.order_by(asc(zero_last), desc(sort_column))
        else:
            query = query.order_by(asc(zero_last), asc(sort_column))
    elif sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    # Apply pagination
    offset = (page - 1) * limit
    vehicles = query.offset(offset).limit(limit).all()

    # Calculate total pages
    total_pages = math.ceil(total / limit) if total > 0 else 0

    response = VehicleListResponse(
        vehicles=[VehicleResponse.model_validate(v) for v in vehicles],
        pagination=PaginationInfo(page=page, limit=limit, total=total, total_pages=total_pages),
    )
    await cache.set(cache_key, response.model_dump(mode="json"), ttl=300)
    return response


@router.get("/exchange-rate")
async def get_exchange_rate(
    base: str = Query("JPY", description="Base currency"),
    symbols: str = Query("LKR", description="Target currency"),
):
    """
    Get latest exchange rate (daily) for currency conversion.

    Uses Frankfurter (ECB reference rates), cached for a few hours.
    """
    cache_key = cache.generate_key("fx_rate", base=base, symbols=symbols, provider=FX_PROVIDER)
    cached_response = await cache.get(cache_key)
    if cached_response:
        return cached_response

    try:
        response = requests.get(
            FX_ENDPOINT,
            params={"base": base, "symbols": symbols},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        rate = data.get("rates", {}).get(symbols)
        payload = {
            "base": data.get("base", base),
            "target": symbols,
            "rate": float(rate) if rate is not None else None,
            "date": data.get("date"),
            "provider": FX_PROVIDER,
            "fetched_at": datetime.utcnow().isoformat(),
        }
        await cache.set(cache_key, payload, ttl=FX_CACHE_TTL_SECONDS)
        return payload
    except Exception as exc:
        fallback_rate = (
            float(DEFAULT_JPY_TO_LKR)
            if base.upper() == "JPY" and symbols.upper() == "LKR"
            else None
        )
        return {
            "base": base,
            "target": symbols,
            "rate": fallback_rate,
            "date": None,
            "provider": "fallback",
            "fetched_at": datetime.utcnow().isoformat(),
            "error": str(exc),
        }


@router.get("/makes/list")
async def list_makes(db: Session = Depends(get_db)):
    """
    Get list of all unique vehicle makes (manufacturers).

    **Returns:**
    - List of unique manufacturers

    **Usage:**
    - For dropdown filters in frontend

    Public endpoint - no authentication required.
    """

    makes = db.query(Vehicle.make).distinct().order_by(Vehicle.make).all()
    return {"makes": [make[0] for make in makes]}


@router.get("/models/list")
async def list_models(
    make: Optional[str] = Query(None, description="Filter models by manufacturer"),
    db: Session = Depends(get_db),
):
    """
    Get list of models, optionally filtered by make.

    **Query Parameters:**
    - `make`: Filter models by manufacturer

    **Returns:**
    - List of unique models

    **Usage:**
    - For dropdown filters in frontend

    Public endpoint - no authentication required.
    """

    query = db.query(Vehicle.model).distinct()

    if make:
        query = query.filter(Vehicle.make.ilike(f"%{make}%"))

    models = query.order_by(Vehicle.model).all()
    return {"models": [model[0] for model in models]}


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific vehicle.

    **Path Parameters:**
    - `vehicle_id`: UUID of the vehicle

    **Returns:**
    - Complete vehicle details

    **Errors:**
    - 404: Vehicle not found

    Public endpoint - no authentication required.
    """

    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Vehicle with ID {vehicle_id} not found"
        )

    return VehicleResponse.model_validate(vehicle)


@router.get("/{vehicle_id}/cost", response_model=CostBreakdown)
async def calculate_cost(
    vehicle_id: UUID,
    exchange_rate: Optional[Decimal] = Query(None, description="Custom JPY to LKR rate"),
    db: Session = Depends(get_db),
):
    """
    Calculate total import cost for a vehicle.

    **Cost Breakdown:**
    1. Vehicle price (JPY → LKR conversion)
    2. Shipping cost
    3. CIF value (Cost + Insurance + Freight)
    4. Customs duty (25% of CIF)
    5. VAT (15% of CIF + Customs)
    6. Total cost in LKR

    **Path Parameters:**
    - `vehicle_id`: UUID of the vehicle

    **Query Parameters:**
    - `exchange_rate`: Optional custom JPY to LKR exchange rate

    **Returns:**
    - Detailed cost breakdown with percentages

    **Errors:**
    - 404: Vehicle not found

    Public endpoint - no authentication required.
    """

    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Vehicle with ID {vehicle_id} not found"
        )

    rate = exchange_rate or DEFAULT_JPY_TO_LKR
    vehicle_price_jpy = Decimal(str(vehicle.price_jpy))
    vehicle_price_lkr = vehicle_price_jpy * rate
    shipping_cost_lkr = calculate_shipping_cost(vehicle)
    cif_value = vehicle_price_lkr + shipping_cost_lkr

    tax_vehicle_type = _map_vehicle_type_to_tax(vehicle)
    tax_fuel_type = _map_fuel_type_to_tax(vehicle)
    engine_cc = int(vehicle.engine_cc or 0)
    motor_power_kw = float(vehicle.motor_power_kw) if vehicle.motor_power_kw is not None else None
    vehicle_age_years = max(date.today().year - int(vehicle.year or date.today().year), 0)
    category_codes = _derive_tax_category_codes(vehicle)

    tax_result = None
    catalog_error: Exception | None = None
    try:
        tax_result = calculate_catalog_tax(
            db=db,
            vehicle=vehicle,
            cif_value_lkr=cif_value,
            vehicle_age_years=float(vehicle_age_years),
            engine_cc=engine_cc,
            motor_power_kw=motor_power_kw,
        )
    except NoTaxRuleError as exc:
        catalog_error = exc

    if tax_result is None:
        try:
            tax_result = calculate_tax(
                db=db,
                vehicle_type=tax_vehicle_type,
                fuel_type=tax_fuel_type,
                engine_cc=engine_cc,
                cif_value=float(cif_value),
                power_kw=motor_power_kw,
                vehicle_age_years=float(vehicle_age_years),
                category_codes=category_codes or None,
            )
        except NoTaxRuleError:
            if catalog_error:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=str(catalog_error)
                )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "No approved gazette tax rule matches this vehicle yet. "
                    "Review and approve the extracted gazette rules from the admin dashboard."
                ),
            )
        except InsufficientVehicleDataError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    port_charges_lkr = calculate_port_charges()
    clearance_fee_lkr = calculate_clearance_fee()
    documentation_fee_lkr = calculate_documentation_fee()

    customs_duty = Decimal(str(tax_result["customs_duty"]))
    surcharge = Decimal(str(tax_result.get("surcharge", 0)))
    excise_duty = Decimal(str(tax_result["excise_duty"]))
    cess = Decimal(str(tax_result["cess"]))
    vat = Decimal(str(tax_result["vat"]))
    pal = Decimal(str(tax_result["pal"]))
    luxury_tax = Decimal(str(tax_result.get("luxury_tax", 0)))

    total_cost = (
        Decimal(str(tax_result["total_landed_cost"]))
        + port_charges_lkr
        + clearance_fee_lkr
        + documentation_fee_lkr
    )

    def calc_percentage(amount: Decimal, total: Decimal) -> Decimal:
        if total == 0:
            return Decimal("0.0")
        return ((amount / total) * 100).quantize(Decimal("0.1"))

    taxes_total = customs_duty + surcharge + excise_duty + cess + vat + pal + luxury_tax
    fees_total = shipping_cost_lkr + port_charges_lkr + clearance_fee_lkr + documentation_fee_lkr

    cost_data = {
        "vehicle_price_jpy": vehicle_price_jpy,
        "vehicle_price_lkr": vehicle_price_lkr,
        "exchange_rate": rate,
        "shipping_cost_lkr": shipping_cost_lkr,
        "customs_duty_lkr": customs_duty,
        "surcharge_lkr": surcharge,
        "excise_duty_lkr": excise_duty,
        "vat_lkr": vat,
        "cess_lkr": cess,
        "pal_lkr": pal,
        "luxury_tax_lkr": luxury_tax,
        "port_charges_lkr": port_charges_lkr,
        "clearance_fee_lkr": clearance_fee_lkr,
        "documentation_fee_lkr": documentation_fee_lkr,
        "total_cost_lkr": total_cost,
        "vehicle_percentage": calc_percentage(vehicle_price_lkr, total_cost),
        "taxes_percentage": calc_percentage(taxes_total, total_cost),
        "fees_percentage": calc_percentage(fees_total, total_cost),
    }

    # Pass Decimals directly; Pydantic handles coercion
    return CostBreakdown(**cost_data)  # type: ignore[arg-type]


# ============================================================================
# ADMIN ENDPOINTS (Requires ADMIN role)
# ============================================================================


@router.post("/scrape-now", status_code=status.HTTP_202_ACCEPTED)
async def trigger_scrape_now(
    current_user=Depends(get_current_admin),
):
    """
    Trigger CD-23 scraping immediately (admin only).
    """
    from app.services.scraper.scheduler import scraper_scheduler

    thread = threading.Thread(target=scraper_scheduler.run_now, daemon=True)
    thread.start()
    return {"message": "Vehicle scraping started", "status": "processing"}


@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    vehicle_data: VehicleCreate,
    current_user=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Create a new vehicle.

    **Request Body:**
    - Vehicle data (see VehicleCreate schema)

    **Returns:**
    - Created vehicle details

    **Errors:**
    - 400: Vehicle with auction_id already exists

    Requires ADMIN role.
    """

    # Check if stock_no already exists
    existing = db.query(Vehicle).filter(Vehicle.stock_no == vehicle_data.stock_no).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vehicle with stock_no '{vehicle_data.stock_no}' already exists",
        )

    # Create vehicle
    vehicle = Vehicle(**vehicle_data.model_dump())

    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    await cache.clear_pattern("vehicles:*")

    return VehicleResponse.model_validate(vehicle)


@router.get("/{vehicle_id}/images")
async def get_vehicle_images(vehicle_id: UUID, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    candidates: list[str] = []
    if vehicle.gallery_images:
        try:
            stored = json.loads(str(vehicle.gallery_images))
            if isinstance(stored, list):
                candidates.extend([str(item) for item in stored if item])
        except Exception:
            pass
    if vehicle.image_url:
        candidates.append(str(vehicle.image_url))
    if vehicle.vehicle_url:
        candidates.extend(_scrape_vehicle_gallery_images(str(vehicle.vehicle_url)))

    def normalize(item: str) -> str:
        full = item.strip()
        if full.startswith(("http://", "https://")):
            lower = full.lower()
            if "/vimgs/medium/" in lower:
                full = full.replace("/VIMGS/medium/", "/VIMGS/images/").replace(
                    "/vimgs/medium/", "/VIMGS/images/"
                )
            if "/vimgs/thumb/" in lower:
                full = full.replace("/VIMGS/thumb/", "/VIMGS/images/").replace(
                    "/vimgs/thumb/", "/VIMGS/images/"
                )
                name = full.rsplit("/", 1)[-1]
                if name.startswith("T"):
                    full = full.rsplit("/", 1)[0] + "/" + name[1:]
        return full

    def key_for(item: str) -> str:
        if item.startswith(("http://", "https://")):
            name = item.rsplit("/", 1)[-1]
            if name.startswith("T"):
                name = name[1:]
            return name.lower()
        return item.lower()

    images: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        if not item:
            continue
        normalized = normalize(item)
        lower = normalized.lower()
        if normalized.startswith(("http://", "https://")):
            if (
                "/vimgs/images/" not in lower
                and "/car_images/" not in lower
                and "/storage/v1/object/public/" not in lower
            ):
                continue
        elif not normalized.startswith(("data/", "/data/")):
            continue
        k = key_for(normalized)
        if k in seen:
            continue
        seen.add(k)
        images.append(normalized)

    return {"vehicle_id": str(vehicle.id), "images": images[:40]}


@router.patch("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: UUID,
    vehicle_data: VehicleUpdate,
    current_user=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Update a vehicle.

    **Path Parameters:**
    - `vehicle_id`: UUID of the vehicle

    **Request Body:**
    - Fields to update (see VehicleUpdate schema)

    **Returns:**
    - Updated vehicle details

    **Errors:**
    - 404: Vehicle not found

    Requires ADMIN role.
    """

    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    # Update fields
    update_data = vehicle_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(vehicle, field, value)

    db.commit()
    db.refresh(vehicle)
    await cache.clear_pattern("vehicles:*")

    return VehicleResponse.model_validate(vehicle)


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(
    vehicle_id: UUID,
    current_user=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Delete a vehicle.

    **Path Parameters:**
    - `vehicle_id`: UUID of the vehicle

    **Returns:**
    - No content (204)

    **Errors:**
    - 404: Vehicle not found
    - 400: Cannot delete vehicle with existing orders

    Requires ADMIN role.
    """

    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    # Check if vehicle has orders
    # TODO: Add this check when Order model is imported
    # if vehicle.orders:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Cannot delete vehicle with existing orders"
    #     )

    db.delete(vehicle)
    db.commit()
    await cache.clear_pattern("vehicles:*")

    return None
