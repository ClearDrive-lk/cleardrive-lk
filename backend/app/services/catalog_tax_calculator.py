"""
Tax calculator based on versioned catalog tables (HS code matrix + global parameters).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.models.tax_rule_catalog import HSCodeMatrixRule
from app.modules.vehicles.models import Vehicle
from app.services.tax_calculator import NoTaxRuleError
from app.services.tax_engine import TaxEngine, TaxEngineLookupError
from sqlalchemy.orm import Session


@dataclass
class CatalogTaxContext:
    hs_rule: HSCodeMatrixRule
    vehicle_type: str
    fuel_type: str
    age_condition: str
    capacity_value: Decimal
    capacity_unit: str


def _normalize_fuel_type(vehicle: Vehicle) -> str:
    raw = str(getattr(vehicle.fuel_type, "value", vehicle.fuel_type) or "").upper()
    if "ELECTRIC" in raw:
        return "ELECTRIC"
    if "DIESEL" in raw:
        return "DIESEL"
    return "PETROL"


def _map_vehicle_type(vehicle: Vehicle) -> str:
    raw_type = vehicle.vehicle_type.value.upper() if vehicle.vehicle_type else ""
    raw_fuel = str(getattr(vehicle.fuel_type, "value", vehicle.fuel_type) or "").upper()

    if "ELECTRIC" in raw_fuel:
        return "ELECTRIC"
    if "HYBRID" in raw_fuel:
        return "HYBRID"

    if raw_type in {"PICKUP"}:
        return "COMMERCIAL_TRUCK"
    if raw_type in {"MACHINERY", "BIKES"}:
        return "SPECIAL_PURPOSE"

    return "PASSENGER_CAR"


def _age_condition_for_depreciation(age_years: float) -> str:
    if age_years <= 1:
        return "<=1"
    if age_years <= 2:
        return ">1-2"
    if age_years <= 3:
        return ">2-3"
    if age_years <= 5:
        return ">3-5"
    if age_years <= 10:
        return ">5-10"
    return ">10"


def _age_condition_candidates_for_hs(age_years: float) -> list[str]:
    if age_years <= 1:
        return ["<=1"]
    if age_years <= 3:
        return [">1-3", ">1-2", ">2-3"]
    if age_years <= 5:
        return [">3-5"]
    if age_years <= 10:
        return [">5-10"]
    return [">10"]


def _resolve_hs_rule(
    db: Session,
    *,
    vehicle_type: str,
    fuel_type: str,
    age_years: float,
    engine_cc: int,
    motor_power_kw: float | None,
) -> CatalogTaxContext:
    engine_value = Decimal(str(engine_cc or 0))
    power_value = Decimal(str(motor_power_kw or 0))

    capacity_candidates: list[tuple[str, Decimal]] = []
    if fuel_type == "ELECTRIC":
        capacity_candidates.append(("KW", power_value))
    capacity_candidates.append(("CC", engine_value))

    engine = TaxEngine(db)
    vehicle_type_candidates = [vehicle_type]
    if vehicle_type != "PASSENGER_CAR":
        vehicle_type_candidates.append("PASSENGER_CAR")

    for candidate_vehicle_type in vehicle_type_candidates:
        for unit, capacity_value in capacity_candidates:
            for age_condition in _age_condition_candidates_for_hs(age_years):
                try:
                    hs_rule = engine.resolve_hs_rule(
                        vehicle_type=candidate_vehicle_type,
                        fuel_type=fuel_type,
                        age_condition=age_condition,
                        capacity_input=capacity_value,
                        capacity_unit=unit,
                    )
                    return CatalogTaxContext(
                        hs_rule=hs_rule,
                        vehicle_type=candidate_vehicle_type,
                        fuel_type=fuel_type,
                        age_condition=age_condition,
                        capacity_value=capacity_value,
                        capacity_unit=unit,
                    )
                except TaxEngineLookupError:
                    continue

    raise NoTaxRuleError(
        "No HS-code matrix rule matches this vehicle. "
        "Review the HS code matrix CSV for matching vehicle_type, fuel_type, age, and capacity."
    )


def _get_global_value(
    engine: TaxEngine, *, group: str, name: str, condition: str, default: Decimal | None = None
) -> Decimal:
    try:
        record = engine.get_global_param(
            parameter_group=group,
            parameter_name=name,
            condition_or_type=condition,
        )
        return Decimal(str(record.value))
    except TaxEngineLookupError:
        if default is not None:
            return default
        raise


def calculate_catalog_tax(
    *,
    db: Session,
    vehicle: Vehicle,
    cif_value_lkr: Decimal,
    vehicle_age_years: float,
    engine_cc: int,
    motor_power_kw: float | None,
) -> dict[str, float]:
    vehicle_type = _map_vehicle_type(vehicle)
    fuel_type = _normalize_fuel_type(vehicle)

    if fuel_type == "ELECTRIC" and motor_power_kw is None:
        # Use 0 as a fallback to allow matching broad electric ranges.
        motor_power_kw = 0.0

    hs_context = _resolve_hs_rule(
        db,
        vehicle_type=vehicle_type,
        fuel_type=fuel_type,
        age_years=vehicle_age_years,
        engine_cc=engine_cc,
        motor_power_kw=motor_power_kw,
    )

    engine = TaxEngine(db)
    depreciation_condition = _age_condition_for_depreciation(vehicle_age_years)
    depreciation_pct = _get_global_value(
        engine,
        group="VALUATION",
        name="DEPRECIATION",
        condition=depreciation_condition,
        default=Decimal("100"),
    )

    uplift_base_pct = _get_global_value(
        engine,
        group="CUSTOMS_RULE",
        name="STATUTORY_UPLIFT_BASE",
        condition="ALL",
        default=Decimal("0"),
    )

    today = date.today()
    if vehicle_age_years <= 1:
        surcharge_condition = "BRAND_NEW"
    elif today < date(2026, 4, 1):
        surcharge_condition = "IMPORT_DATE<2026-04-01"
    else:
        surcharge_condition = "USED_AND_AFTER_2026-04-01"

    surcharge_rate = _get_global_value(
        engine,
        group="CUSTOMS_RULE",
        name="SURCHARGE_RATE",
        condition=surcharge_condition,
        default=Decimal("0"),
    )

    vat_rate = _get_global_value(
        engine,
        group="GENERAL_TAX",
        name="VAT",
        condition="STANDARD_RATE",
        default=Decimal("15"),
    )
    sscl_rate = _get_global_value(
        engine,
        group="GENERAL_TAX",
        name="SSCL",
        condition="EFFECTIVE_FROM_APRIL_1_2026",
        default=Decimal("0"),
    )

    luxury_threshold = Decimal("0")
    luxury_rate = Decimal("0")
    if vehicle_type == "ELECTRIC":
        luxury_threshold = _get_global_value(
            engine,
            group="LUXURY_TAX",
            name="THRESHOLD_EV",
            condition="ELECTRIC",
            default=Decimal("0"),
        )
        luxury_rate = _get_global_value(
            engine,
            group="LUXURY_TAX",
            name="RATE_EV",
            condition="ON_EXCESS_VALUE",
            default=Decimal("0"),
        )
    elif vehicle_type == "HYBRID":
        luxury_threshold = _get_global_value(
            engine,
            group="LUXURY_TAX",
            name="THRESHOLD_HYBRID_PETROL"
            if fuel_type == "PETROL"
            else "THRESHOLD_HYBRID_DIESEL",
            condition="HYBRID",
            default=Decimal("0"),
        )
        luxury_rate = _get_global_value(
            engine,
            group="LUXURY_TAX",
            name="RATE_HYBRID_PETROL" if fuel_type == "PETROL" else "RATE_HYBRID_DIESEL",
            condition="ON_EXCESS_VALUE",
            default=Decimal("0"),
        )
    else:
        luxury_threshold = _get_global_value(
            engine,
            group="LUXURY_TAX",
            name="THRESHOLD_DIESEL" if fuel_type == "DIESEL" else "THRESHOLD_PETROL",
            condition="PASSENGER_CAR",
            default=Decimal("0"),
        )
        luxury_rate = _get_global_value(
            engine,
            group="LUXURY_TAX",
            name="RATE_DIESEL" if fuel_type == "DIESEL" else "RATE_PETROL",
            condition="ON_EXCESS_VALUE",
            default=Decimal("0"),
        )

    depreciated_value = cif_value_lkr * (depreciation_pct / Decimal("100"))
    uplifted_value = depreciated_value * (Decimal("1") + uplift_base_pct / Decimal("100"))

    customs_duty = uplifted_value * (Decimal(str(hs_context.hs_rule.cid_pct)) / Decimal("100"))
    surcharge = customs_duty * (surcharge_rate / Decimal("100"))
    excise_duty = hs_context.capacity_value * Decimal(str(hs_context.hs_rule.excise_unit_rate_lkr))
    pal = uplifted_value * (Decimal(str(hs_context.hs_rule.pal_pct)) / Decimal("100"))
    cess = uplifted_value * (Decimal(str(hs_context.hs_rule.cess_pct)) / Decimal("100"))

    excess_value = max(uplifted_value - luxury_threshold, Decimal("0"))
    luxury_tax = excess_value * (luxury_rate / Decimal("100")) if luxury_rate else Decimal("0")

    vat_base = uplifted_value + customs_duty + surcharge + excise_duty + pal + cess + luxury_tax
    vat = vat_base * (vat_rate / Decimal("100"))
    sscl = vat_base * (sscl_rate / Decimal("100"))

    total_duty = customs_duty + surcharge + excise_duty + pal + cess + luxury_tax + vat + sscl
    total_landed_cost = uplifted_value + total_duty
    effective_rate = (total_duty / uplifted_value * Decimal("100")) if uplifted_value > 0 else 0

    return {
        "cif_value": float(uplifted_value),
        "customs_duty": float(customs_duty),
        "surcharge": float(surcharge),
        "excise_duty": float(excise_duty),
        "cess": float(cess),
        "vat": float(vat + sscl),
        "pal": float(pal),
        "luxury_tax": float(luxury_tax),
        "total_duty": float(total_duty),
        "total_landed_cost": float(total_landed_cost),
        "effective_rate_percent": float(effective_rate),
        "rule_used": {
            "rule_source": "CATALOG",
            "vehicle_type": hs_context.vehicle_type,
            "fuel_type": hs_context.fuel_type,
            "age_condition": hs_context.age_condition,
            "capacity_unit": hs_context.capacity_unit,
            "hs_code": hs_context.hs_rule.hs_code,
        },
    }
