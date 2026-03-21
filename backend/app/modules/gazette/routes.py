"""
Gazette upload and extraction endpoints.
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Mapping
from uuid import UUID

from app.core.config import settings
from app.core.database import get_db
from app.core.permissions import Permission, require_permission
from app.models.audit_log import AuditEventType, AuditLog
from app.models.gazette import (
    ApplyOn,
    CessType,
    CustomsRule,
    Gazette,
    GazetteStatus,
    LuxuryTaxRule,
    SurchargeRule,
    TaxFuelType,
    TaxRule,
    TaxVehicleType,
    VehicleTaxRule,
)
from app.models.tax_rule_catalog import GlobalTaxParameter, HSCodeMatrixRule
from app.modules.auth.models import User
from app.services.document_ai import document_ai_service
from app.services.gazette_fallback_parser import (
    canonicalize_electric_vehicle_rule,
    parse_ocr_to_rules,
    sanitize_electric_vehicle_rules,
)
from app.services.gemini import gemini_service
from app.services.rule_versioning import RuleVersioningService
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

router = APIRouter(prefix="/gazette", tags=["Gazette"])
logger = logging.getLogger(__name__)


class GazetteUploadResponse(BaseModel):
    gazette_id: str
    gazette_no: str
    effective_date: str | None
    rules_count: int
    confidence: float
    status: str
    preview: dict[str, Any]
    message: str | None = None


class CatalogUploadResponse(BaseModel):
    dataset: str
    effective_date: str
    uploaded_rows: int
    superseded_rows: int
    preview_rows: list[dict[str, Any]]
    message: str


class CatalogRowUpdateRequest(BaseModel):
    values: dict[str, Any]
    change_reason: str | None = None


class GazetteDecisionRequest(BaseModel):
    reason: str | None = None


class GazetteRuleInput(BaseModel):
    rule_type: str | None = None
    vehicle_type: str | None = None
    fuel_type: str | None = None
    category_code: str | None = None
    hs_code: str | None = None
    engine_min: int = 0
    engine_max: int = 999999
    power_kw_min: Decimal | None = None
    power_kw_max: Decimal | None = None
    age_years_min: Decimal | None = None
    age_years_max: Decimal | None = None
    excise_type: str | None = None
    excise_rate: Decimal | None = None
    customs_percent: Decimal | None = Decimal("0")
    surcharge_percent: Decimal | None = Decimal("0")
    excise_percent: Decimal | None = Decimal("0")
    excise_per_kw_amount: Decimal | None = None
    vat_percent: Decimal | None = Decimal("15")
    pal_percent: Decimal | None = Decimal("0")
    cess_percent: Decimal | None = Decimal("0")
    cess_type: str | None = None
    cess_value: Decimal | None = None
    luxury_tax_threshold: Decimal | None = None
    luxury_tax_percent: Decimal | None = None
    threshold_value: Decimal | None = None
    rate_percent: Decimal | None = None
    applies_to: str | None = None
    name: str | None = None
    apply_on: str = ApplyOn.CIF.value
    notes: str | None = None


class GazetteReviewUpdateRequest(BaseModel):
    effective_date: str | None = None
    rules: list[GazetteRuleInput] = Field(default_factory=list)


class CatalogReviewUpdateRequest(BaseModel):
    effective_date: str | None = None
    rows: list[dict[str, Any]] = Field(default_factory=list)
    change_reason: str | None = None


class GazetteHistoryItem(BaseModel):
    id: str
    gazette_no: str
    effective_date: str | None
    status: str
    rules_count: int
    created_at: datetime
    uploaded_by: str | None
    approved_by: str | None
    rejection_reason: str | None


class GazetteHistoryResponse(BaseModel):
    items: list[GazetteHistoryItem]
    total: int
    page: int
    limit: int
    total_pages: int


class GazetteDetailResponse(BaseModel):
    gazette_id: str
    gazette_no: str
    effective_date: str | None
    rules_count: int
    status: str
    preview: dict[str, Any]
    rejection_reason: str | None
    uploaded_by: str | None
    approved_by: str | None
    created_at: datetime


def _parse_effective_date(raw_value: Any) -> date | None:
    if raw_value is None:
        return None
    value = str(raw_value).strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _parse_int(value: Any, default: int = 0) -> int:
    if value in (None, ""):
        return default
    return int(str(value).strip())


def _parse_csv_decimal(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    return Decimal(str(value).strip())


def _csv_value(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return None


def _json_safe_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {key: _json_safe_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe_value(item) for item in value]
    return value


def _read_catalog_csv_rows(content: bytes) -> list[list[str]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV file must be UTF-8 encoded") from exc

    parsed_rows: list[list[str]] = []
    for raw_row in csv.reader(io.StringIO(text)):
        if not raw_row:
            continue
        normalized_row = [str(cell or "").strip() for cell in raw_row]
        if len(normalized_row) == 1 and "," in normalized_row[0]:
            normalized_row = [cell.strip() for cell in next(csv.reader([normalized_row[0]]))]
        if not any(normalized_row):
            continue
        parsed_rows.append(normalized_row)

    if not parsed_rows:
        raise HTTPException(status_code=400, detail="CSV file has no rows")
    return parsed_rows


def _parse_global_tax_parameter_rows(content: bytes) -> list[dict[str, Any]]:
    rows = _read_catalog_csv_rows(content)
    header = rows[0]
    expected = [
        "parameter_group",
        "parameter_name",
        "condition_or_type",
        "value",
        "unit",
        "calculation_order",
        "applicability_flag",
    ]
    if header != expected:
        raise HTTPException(
            status_code=400,
            detail=("Invalid global_tax_parameters CSV header. Expected: " + ", ".join(expected)),
        )

    parsed: list[dict[str, Any]] = []
    for index, row in enumerate(rows[1:], start=2):
        if len(row) != len(expected):
            raise HTTPException(status_code=400, detail=f"Invalid CSV shape on row {index}")
        raw = dict(zip(expected, row, strict=False))
        try:
            parsed.append(
                {
                    "parameter_group": raw["parameter_group"].strip().upper(),
                    "parameter_name": raw["parameter_name"].strip().upper(),
                    "condition_or_type": raw["condition_or_type"].strip().upper(),
                    "value": Decimal(raw["value"].strip()),
                    "unit": raw["unit"].strip().upper(),
                    "calculation_order": int(raw["calculation_order"].strip()),
                    "applicability_flag": raw["applicability_flag"].strip().upper() or None,
                }
            )
        except Exception as exc:
            raise HTTPException(
                status_code=400, detail=f"Invalid CSV value on row {index}"
            ) from exc
    if not parsed:
        raise HTTPException(status_code=400, detail="CSV file has no tax rules")
    return parsed


def _parse_hs_code_matrix_rows(content: bytes) -> list[dict[str, Any]]:
    rows = _read_catalog_csv_rows(content)
    expected = [
        "vehicle_type",
        "fuel_type",
        "age_condition",
        "hs_code",
        "capacity_min",
        "capacity_max",
        "capacity_unit",
        "cid_pct",
        "pal_pct",
        "cess_pct",
        "excise_unit_rate_lkr",
    ]
    optional_fields = ["min_excise_flat_rate_lkr"]
    header_aliases = {
        "customs_pct": "cid_pct",
        "customs_percent": "cid_pct",
        "excise_rate": "excise_unit_rate_lkr",
        "excise_rate_lkr": "excise_unit_rate_lkr",
    }
    header = [
        header_aliases.get(str(cell or "").strip().lower(), str(cell or "").strip().lower())
        for cell in rows[0]
    ]
    if header[: len(expected)] != expected:
        raise HTTPException(
            status_code=400,
            detail=("Invalid hs_code_matrix CSV header. Expected: " + ", ".join(expected)),
        )

    parsed: list[dict[str, Any]] = []
    for index, row in enumerate(rows[1:], start=2):
        if len(row) < len(expected):
            raise HTTPException(status_code=400, detail=f"Invalid CSV shape on row {index}")
        field_order = list(expected)
        if len(header) > len(expected) and header[len(expected)] == optional_fields[0]:
            field_order.append(optional_fields[0])
        raw = dict(zip(field_order, row[: len(field_order)], strict=False))
        try:
            parsed.append(
                {
                    "vehicle_type": raw["vehicle_type"].strip().upper(),
                    "fuel_type": raw["fuel_type"].strip().upper(),
                    "age_condition": raw["age_condition"].strip().upper(),
                    "hs_code": raw["hs_code"].strip(),
                    "capacity_min": Decimal(raw["capacity_min"].strip()),
                    "capacity_max": Decimal(raw["capacity_max"].strip()),
                    "capacity_unit": raw["capacity_unit"].strip().upper(),
                    "cid_pct": Decimal(raw["cid_pct"].strip()),
                    "pal_pct": Decimal(raw["pal_pct"].strip()),
                    "cess_pct": Decimal(raw["cess_pct"].strip()),
                    "excise_unit_rate_lkr": Decimal(raw["excise_unit_rate_lkr"].strip()),
                    "min_excise_flat_rate_lkr": Decimal(
                        raw.get("min_excise_flat_rate_lkr", "0").strip() or "0"
                    ),
                }
            )
        except Exception as exc:
            raise HTTPException(
                status_code=400, detail=f"Invalid CSV value on row {index}"
            ) from exc
    if not parsed:
        raise HTTPException(status_code=400, detail="CSV file has no tax rules")
    return parsed


def _serialize_catalog_record(record: Any, dataset: str) -> dict[str, Any]:
    if dataset == "global_tax_parameters":
        return {
            "id": str(record.id),
            "parameter_group": record.parameter_group,
            "parameter_name": record.parameter_name,
            "condition_or_type": record.condition_or_type,
            "value": float(record.value),
            "unit": record.unit,
            "calculation_order": record.calculation_order,
            "applicability_flag": record.applicability_flag,
            "effective_date": record.effective_date.isoformat(),
            "version": record.version,
            "is_active": record.is_active,
        }
    return {
        "id": str(record.id),
        "vehicle_type": record.vehicle_type,
        "fuel_type": record.fuel_type,
        "age_condition": record.age_condition,
        "hs_code": record.hs_code,
        "capacity_min": float(record.capacity_min),
        "capacity_max": float(record.capacity_max),
        "capacity_unit": record.capacity_unit,
        "cid_pct": float(record.cid_pct),
        "pal_pct": float(record.pal_pct),
        "cess_pct": float(record.cess_pct),
        "excise_unit_rate_lkr": float(record.excise_unit_rate_lkr),
        "min_excise_flat_rate_lkr": float(record.min_excise_flat_rate_lkr),
        "effective_date": record.effective_date.isoformat(),
        "version": record.version,
        "is_active": record.is_active,
    }


def _parse_csv_rules(content: bytes) -> tuple[date | None, list[dict[str, Any]]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV file must be UTF-8 encoded") from exc

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV file must include a header row")

    rules: list[dict[str, Any]] = []
    effective_dates: set[date] = set()

    for index, raw_row in enumerate(reader, start=2):
        row = {str(key or "").strip(): value for key, value in raw_row.items()}
        if not any(str(value or "").strip() for value in row.values()):
            continue

        try:
            effective_date = _parse_effective_date(row.get("effective_date"))
            if effective_date is not None:
                effective_dates.add(effective_date)

            rules.append(
                {
                    "rule_type": str(_csv_value(row, "rule_type") or "VEHICLE_TAX").strip().upper(),
                    "vehicle_type": (
                        str(_csv_value(row, "vehicle_type") or "").strip().upper() or None
                    ),
                    "fuel_type": str(_csv_value(row, "fuel_type") or "").strip().upper() or None,
                    "category_code": (
                        str(_csv_value(row, "category_code") or "").strip().upper() or None
                    ),
                    "hs_code": str(_csv_value(row, "hs_code") or "").strip() or None,
                    "engine_min": _parse_int(_csv_value(row, "engine_min"), 0),
                    "engine_max": _parse_int(_csv_value(row, "engine_max"), 999999),
                    "power_kw_min": _parse_csv_decimal(
                        _csv_value(row, "power_kw_min", "power_min_kw")
                    ),
                    "power_kw_max": _parse_csv_decimal(
                        _csv_value(row, "power_kw_max", "power_max_kw")
                    ),
                    "age_years_min": _parse_csv_decimal(
                        _csv_value(row, "age_years_min", "age_min_years")
                    ),
                    "age_years_max": _parse_csv_decimal(
                        _csv_value(row, "age_years_max", "age_max_years")
                    ),
                    "excise_type": (
                        str(_csv_value(row, "excise_type") or "").strip().upper() or None
                    ),
                    "excise_rate": _parse_csv_decimal(_csv_value(row, "excise_rate")),
                    "excise_per_kw_amount": _parse_csv_decimal(
                        _csv_value(row, "excise_per_kw_amount")
                    ),
                    "customs_percent": _parse_csv_decimal(_csv_value(row, "customs_percent")),
                    "surcharge_percent": _parse_csv_decimal(_csv_value(row, "surcharge_percent")),
                    "excise_percent": _parse_csv_decimal(_csv_value(row, "excise_percent")),
                    "vat_percent": _parse_csv_decimal(_csv_value(row, "vat_percent")),
                    "pal_percent": _parse_csv_decimal(_csv_value(row, "pal_percent")),
                    "cess_percent": _parse_csv_decimal(_csv_value(row, "cess_percent")),
                    "cess_type": str(_csv_value(row, "cess_type") or "").strip().upper() or None,
                    "cess_value": _parse_csv_decimal(_csv_value(row, "cess_value")),
                    "luxury_tax_threshold": _parse_csv_decimal(
                        _csv_value(row, "luxury_tax_threshold")
                    ),
                    "luxury_tax_percent": _parse_csv_decimal(_csv_value(row, "luxury_tax_percent")),
                    "threshold_value": _parse_csv_decimal(_csv_value(row, "threshold_value")),
                    "rate_percent": _parse_csv_decimal(_csv_value(row, "rate_percent")),
                    "applies_to": str(_csv_value(row, "applies_to") or "").strip().upper() or None,
                    "name": str(_csv_value(row, "name") or "").strip() or None,
                    "apply_on": (
                        str(_csv_value(row, "apply_on") or ApplyOn.CIF.value).strip().upper()
                    ),
                    "notes": str(_csv_value(row, "notes") or "").strip() or None,
                }
            )
        except Exception as exc:
            raise HTTPException(
                status_code=400, detail=f"Invalid CSV value on row {index}"
            ) from exc

    if not rules:
        raise HTTPException(status_code=400, detail="CSV file has no tax rules")

    if len(effective_dates) > 1:
        raise HTTPException(
            status_code=400,
            detail="CSV file contains multiple effective_date values",
        )

    return (next(iter(effective_dates)) if effective_dates else None, rules)


def _sanitize_extracted_payload(payload: dict[str, Any]) -> dict[str, Any]:
    sanitized = dict(payload)
    raw_rules = sanitized.get("rules")
    if not isinstance(raw_rules, list):
        return sanitized

    raw_text = str(sanitized.get("text") or "")
    electric_rules = sanitize_electric_vehicle_rules(raw_rules, raw_text)
    if electric_rules is None:
        return sanitized

    non_vehicle_rules = [
        rule
        for rule in raw_rules
        if isinstance(rule, dict) and _infer_rule_type(rule) != "VEHICLE_TAX"
    ]
    sanitized["rules"] = [*electric_rules, *non_vehicle_rules]
    return sanitized


def _is_catalog_payload(payload: Mapping[str, Any]) -> bool:
    return str(payload.get("source") or "").startswith("CATALOG_")


def _catalog_rows(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_rows = payload.get("catalog_rows")
    return [row for row in raw_rows if isinstance(row, dict)] if isinstance(raw_rows, list) else []


def _review_item_count(payload: Mapping[str, Any]) -> int:
    raw_rules = payload.get("rules")
    if isinstance(raw_rules, list):
        return len(raw_rules)
    return len(_catalog_rows(payload))


def _catalog_gazette_no(prefix: str, effective_date: date) -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"CATALOG/{prefix}/{effective_date.isoformat()}/{timestamp}"


def _coerce_decimal(value: Any, default: str = "0") -> Decimal:
    if value is None or value == "":
        return Decimal(default)
    return Decimal(str(value))


def _coerce_optional_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    return Decimal(str(value))


def _rule_value(rule: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in rule and rule[key] not in (None, ""):
            return rule[key]
    return None


def _parse_gazette_id(gazette_id: str) -> UUID:
    try:
        return UUID(gazette_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid gazette_id") from exc


def _slug_category_code(value: str) -> str | None:
    normalized = "".join(char if char.isalnum() else "_" for char in value.upper())
    collapsed = "_".join(part for part in normalized.split("_") if part)
    return collapsed or None


def _normalize_fuel_type(raw_value: Any) -> str:
    value = str(raw_value or "").strip().upper()
    if not value:
        raise ValueError("fuel_type is required")
    if value in {member.value for member in TaxFuelType}:
        return value
    if "HYBRID" in value:
        return TaxFuelType.HYBRID.value
    if "DIESEL" in value:
        return TaxFuelType.DIESEL.value
    if "ELECTRIC" in value:
        return TaxFuelType.ELECTRIC.value
    if "GASOLINE" in value or "PETROL" in value:
        return TaxFuelType.PETROL.value
    return TaxFuelType.OTHER.value


def _normalize_vehicle_type(raw_value: Any, fuel_type: str) -> tuple[str, str | None]:
    value = str(raw_value or "").strip()
    if not value:
        raise ValueError("vehicle_type is required")

    upper_value = value.upper()
    if upper_value in {member.value for member in TaxVehicleType}:
        return upper_value, None

    category_code = _slug_category_code(value)
    normalized = upper_value.replace("-", " ")
    if "SUV" in normalized:
        return TaxVehicleType.SUV.value, category_code
    if "SEDAN" in normalized:
        return TaxVehicleType.SEDAN.value, category_code
    if "TRUCK" in normalized or "GOODS VEHICLE" in normalized or "PICKUP" in normalized:
        return TaxVehicleType.TRUCK.value, category_code
    if "VAN" in normalized or "MINIVAN" in normalized:
        return TaxVehicleType.VAN.value, category_code
    if "MOTORCYCLE" in normalized or "BIKE" in normalized:
        return TaxVehicleType.MOTORCYCLE.value, category_code
    if fuel_type == TaxFuelType.ELECTRIC.value or "ELECTRIC" in normalized:
        return TaxVehicleType.ELECTRIC.value, category_code
    return TaxVehicleType.OTHER.value, category_code


def _normalize_vehicle_type_for_rule(
    raw_rule: dict[str, Any], fuel_type: str
) -> tuple[str, str | None]:
    raw_vehicle_type = raw_rule.get("vehicle_type")
    if raw_vehicle_type not in (None, ""):
        return _normalize_vehicle_type(raw_vehicle_type, fuel_type)

    inferred_category_code = _slug_category_code(str(raw_rule.get("category_code") or ""))
    inferred_hs_code = str(raw_rule.get("hs_code") or "").strip()
    if inferred_category_code:
        if "GOODS" in inferred_category_code or inferred_hs_code.startswith("8704.60."):
            return TaxVehicleType.TRUCK.value, inferred_category_code
        if "TRISHAW" in inferred_category_code:
            return TaxVehicleType.OTHER.value, inferred_category_code
    if fuel_type == TaxFuelType.ELECTRIC.value:
        return TaxVehicleType.ELECTRIC.value, inferred_category_code
    raise ValueError("vehicle_type is required")


def _get_power_kw_min(rule: dict[str, Any]) -> Decimal | None:
    return _coerce_optional_decimal(_rule_value(rule, "power_kw_min", "power_min_kw"))


def _get_power_kw_max(rule: dict[str, Any]) -> Decimal | None:
    if ("power_kw_max" in rule and rule.get("power_kw_max") in (None, "")) or (
        "power_max_kw" in rule and rule.get("power_max_kw") in (None, "")
    ):
        return Decimal("999999")
    return _coerce_optional_decimal(_rule_value(rule, "power_kw_max", "power_max_kw"))


def _get_age_years_min(rule: dict[str, Any]) -> Decimal | None:
    return _coerce_optional_decimal(_rule_value(rule, "age_years_min", "age_min_years"))


def _get_age_years_max(rule: dict[str, Any]) -> Decimal | None:
    if ("age_years_max" in rule and rule.get("age_years_max") in (None, "")) or (
        "age_max_years" in rule and rule.get("age_max_years") in (None, "")
    ):
        return Decimal("999")
    return _coerce_optional_decimal(_rule_value(rule, "age_years_max", "age_max_years"))


def _infer_rule_type(rule: dict[str, Any]) -> str:
    explicit = str(rule.get("rule_type") or "").strip().upper()
    if explicit:
        return explicit

    if rule.get("threshold_value") not in (None, "") or rule.get("luxury_tax_threshold") not in (
        None,
        "",
    ):
        return "LUXURY"
    if str(rule.get("applies_to") or "").strip().upper() == "CUSTOMS_DUTY":
        return "SURCHARGE"
    if (
        rule.get("category_code")
        or _rule_value(rule, "power_kw_min", "power_min_kw") is not None
        or _rule_value(rule, "power_kw_max", "power_max_kw") is not None
        or _rule_value(rule, "age_years_min", "age_min_years") is not None
        or _rule_value(rule, "age_years_max", "age_max_years") is not None
        or rule.get("excise_rate") not in (None, "")
        or rule.get("excise_per_kw_amount") not in (None, "")
        or str(rule.get("excise_type") or "").strip().upper() == "PER_KW"
    ):
        return "VEHICLE_TAX"
    if rule.get("hs_code") and any(
        rule.get(field) not in (None, "")
        for field in ("customs_percent", "vat_percent", "pal_percent", "cess_percent", "cess_value")
    ):
        return "CUSTOMS"
    return "VEHICLE_TAX"


def _parse_tax_rules(gazette: Gazette, approved_by: User) -> list[TaxRule]:
    normalized_rules = _extract_normalized_rules(gazette)
    return _build_tax_rule_rows(
        gazette_id=gazette.id,
        approved_by=approved_by,
        merged_rules=normalized_rules,
    )


def _extract_normalized_rules(gazette: Gazette) -> list[dict[str, Any]]:
    payload = _sanitize_extracted_payload(gazette.raw_extracted or {})
    raw_rules = payload.get("rules")
    if not isinstance(raw_rules, list) or not raw_rules:
        raise HTTPException(status_code=400, detail="Gazette has no extracted tax rules to approve")

    effective_date = gazette.effective_date or _parse_effective_date(payload.get("effective_date"))
    if effective_date is None:
        raise HTTPException(
            status_code=400, detail="Gazette effective date is required for approval"
        )

    rules: list[dict[str, Any]] = []
    for rule in raw_rules:
        if _infer_rule_type(rule) != "VEHICLE_TAX":
            continue
        try:
            fuel_type = _normalize_fuel_type(rule.get("fuel_type"))
            vehicle_type, inferred_category_code = _normalize_vehicle_type_for_rule(rule, fuel_type)
            raw_apply_on = rule.get("apply_on")
            apply_on = (
                ApplyOn(str(raw_apply_on).upper()).value if raw_apply_on not in (None, "") else None
            )
        except Exception as exc:
            raise HTTPException(
                status_code=400, detail="Gazette contains invalid tax rule values"
            ) from exc

        rules.append(
            {
                "vehicle_type": vehicle_type,
                "fuel_type": fuel_type,
                "rule_type": "VEHICLE_TAX",
                "category_code": str(rule.get("category_code") or inferred_category_code or "")
                or None,
                "hs_code": str(rule.get("hs_code") or "") or None,
                "engine_min": int(rule.get("engine_min", 0) or 0),
                "engine_max": int(rule.get("engine_max", 999999) or 999999),
                "power_kw_min": _get_power_kw_min(rule),
                "power_kw_max": _get_power_kw_max(rule),
                "age_years_min": _get_age_years_min(rule),
                "age_years_max": _get_age_years_max(rule),
                "customs_percent": (
                    _coerce_decimal(rule.get("customs_percent"))
                    if rule.get("customs_percent") not in (None, "")
                    else None
                ),
                "surcharge_percent": (
                    _coerce_decimal(rule.get("surcharge_percent"))
                    if rule.get("surcharge_percent") not in (None, "")
                    else None
                ),
                "excise_percent": (
                    _coerce_decimal(rule.get("excise_percent"))
                    if rule.get("excise_percent") not in (None, "")
                    else None
                ),
                "excise_type": str(rule.get("excise_type") or "").strip().upper() or None,
                "excise_rate": _coerce_optional_decimal(rule.get("excise_rate")),
                "excise_per_kw_amount": _coerce_optional_decimal(rule.get("excise_per_kw_amount")),
                "vat_percent": (
                    _coerce_decimal(rule.get("vat_percent"))
                    if rule.get("vat_percent") not in (None, "")
                    else None
                ),
                "pal_percent": (
                    _coerce_decimal(rule.get("pal_percent"))
                    if rule.get("pal_percent") not in (None, "")
                    else None
                ),
                "cess_percent": (
                    _coerce_decimal(rule.get("cess_percent"))
                    if rule.get("cess_percent") not in (None, "")
                    else None
                ),
                "cess_type": str(rule.get("cess_type") or "").strip().upper() or None,
                "cess_value": _coerce_optional_decimal(rule.get("cess_value")),
                "luxury_tax_threshold": _coerce_optional_decimal(rule.get("luxury_tax_threshold")),
                "luxury_tax_percent": _coerce_optional_decimal(rule.get("luxury_tax_percent")),
                "apply_on": apply_on,
                "effective_date": effective_date,
                "notes": str(rule.get("notes") or "") or None,
            }
        )
    return rules


def _extract_dedicated_rule_entries(gazette: Gazette) -> list[dict[str, Any]]:
    payload = _sanitize_extracted_payload(gazette.raw_extracted or {})
    raw_rules = payload.get("rules")
    if not isinstance(raw_rules, list) or not raw_rules:
        raise HTTPException(status_code=400, detail="Gazette has no extracted tax rules to approve")

    effective_date = gazette.effective_date or _parse_effective_date(payload.get("effective_date"))
    if effective_date is None:
        raise HTTPException(
            status_code=400, detail="Gazette effective date is required for approval"
        )

    entries: list[dict[str, Any]] = []
    for raw_rule in raw_rules:
        if not isinstance(raw_rule, dict):
            continue
        rule_type = _infer_rule_type(raw_rule)
        notes = str(raw_rule.get("notes") or "") or None

        if rule_type == "VEHICLE_TAX":
            canonical_electric_rule = canonicalize_electric_vehicle_rule(raw_rule)
            vehicle_rule = (
                {**raw_rule, **canonical_electric_rule}
                if canonical_electric_rule is not None
                else raw_rule
            )
            fuel_type = _normalize_fuel_type(vehicle_rule.get("fuel_type"))
            vehicle_type, inferred_category_code = _normalize_vehicle_type_for_rule(
                vehicle_rule, fuel_type
            )
            power_kw_min = _get_power_kw_min(vehicle_rule)
            power_kw_max = _get_power_kw_max(vehicle_rule)
            age_years_min = _get_age_years_min(vehicle_rule)
            age_years_max = _get_age_years_max(vehicle_rule)
            hs_code = str(vehicle_rule.get("hs_code") or "").strip()
            excise_type = str(vehicle_rule.get("excise_type") or "").strip().upper() or None
            excise_rate = _coerce_optional_decimal(vehicle_rule.get("excise_rate"))
            excise_per_kw_amount = _coerce_optional_decimal(
                vehicle_rule.get("excise_per_kw_amount")
            )
            if excise_type is None:
                if excise_per_kw_amount is not None:
                    excise_type = "PER_KW"
                    excise_rate = excise_per_kw_amount
                elif vehicle_rule.get("excise_percent") not in (None, ""):
                    excise_type = "PERCENTAGE"
                    excise_rate = _coerce_decimal(vehicle_rule.get("excise_percent"))

            category_code = (
                str(vehicle_rule.get("category_code") or inferred_category_code or "") or None
            )
            is_dedicated_vehicle_rule = (
                fuel_type == TaxFuelType.ELECTRIC.value
                or category_code is not None
                or hs_code != ""
                or power_kw_min is not None
                or power_kw_max is not None
                or age_years_min is not None
                or age_years_max is not None
                or vehicle_rule.get("excise_rate") not in (None, "")
                or vehicle_rule.get("excise_per_kw_amount") not in (None, "")
                or excise_type == "PER_KW"
            )
            if not is_dedicated_vehicle_rule:
                continue
            if not category_code:
                raise HTTPException(
                    status_code=400, detail="Vehicle tax rule is missing category_code"
                )
            if (
                power_kw_min is None
                or power_kw_max is None
                or age_years_min is None
                or age_years_max is None
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Vehicle tax rule is missing power or age ranges: "
                        + _format_vehicle_rule_identity(
                            category_code=category_code,
                            fuel_type=fuel_type,
                            hs_code=hs_code,
                            power_kw_min=power_kw_min,
                            power_kw_max=power_kw_max,
                            age_years_min=age_years_min,
                            age_years_max=age_years_max,
                        )
                    ),
                )
            if excise_type is None or excise_rate is None:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Vehicle tax rule is missing excise values: "
                        + _format_vehicle_rule_identity(
                            category_code=category_code,
                            fuel_type=fuel_type,
                            hs_code=hs_code,
                            power_kw_min=power_kw_min,
                            power_kw_max=power_kw_max,
                            age_years_min=age_years_min,
                            age_years_max=age_years_max,
                        )
                    ),
                )
            if not hs_code:
                continue

            entries.append(
                {
                    "rule_type": "VEHICLE_TAX",
                    "vehicle_type": vehicle_type,
                    "fuel_type": fuel_type,
                    "category_code": category_code,
                    "hs_code": hs_code,
                    "power_kw_min": power_kw_min,
                    "power_kw_max": power_kw_max,
                    "age_years_min": age_years_min,
                    "age_years_max": age_years_max,
                    "excise_type": excise_type,
                    "excise_rate": excise_rate,
                    "effective_date": effective_date,
                    "notes": notes,
                }
            )
            continue

        if rule_type == "CUSTOMS":
            hs_code = str(raw_rule.get("hs_code") or "").strip()
            if not hs_code:
                continue
            cess_type = str(raw_rule.get("cess_type") or "").strip().upper() or None
            cess_value = _coerce_optional_decimal(raw_rule.get("cess_value"))
            if cess_type is None:
                if raw_rule.get("cess_percent") not in (None, ""):
                    cess_type = CessType.PERCENT.value
                    cess_value = _coerce_decimal(raw_rule.get("cess_percent"))
                elif cess_value is not None:
                    cess_type = CessType.FIXED.value
            if cess_type is None or cess_value is None:
                cess_type = CessType.PERCENT.value
                cess_value = Decimal("0")
            entries.append(
                {
                    "rule_type": "CUSTOMS",
                    "hs_code": hs_code,
                    "customs_percent": _coerce_decimal(raw_rule.get("customs_percent")),
                    "vat_percent": _coerce_decimal(raw_rule.get("vat_percent")),
                    "pal_percent": _coerce_decimal(raw_rule.get("pal_percent")),
                    "cess_type": cess_type,
                    "cess_value": cess_value,
                    "effective_date": effective_date,
                    "notes": notes,
                }
            )
            continue

        if rule_type == "SURCHARGE":
            rate_percent = _coerce_optional_decimal(
                raw_rule.get("rate_percent", raw_rule.get("surcharge_percent"))
            )
            if rate_percent is None:
                continue
            entries.append(
                {
                    "rule_type": "SURCHARGE",
                    "name": str(raw_rule.get("name") or "CUSTOMS_SURCHARGE"),
                    "rate_percent": rate_percent,
                    "applies_to": str(raw_rule.get("applies_to") or "CUSTOMS_DUTY"),
                    "effective_date": effective_date,
                    "notes": notes,
                }
            )
            continue

        if rule_type == "LUXURY":
            hs_code = str(raw_rule.get("hs_code") or "").strip()
            threshold_value = _coerce_optional_decimal(
                raw_rule.get("threshold_value", raw_rule.get("luxury_tax_threshold"))
            )
            rate_percent = _coerce_optional_decimal(
                raw_rule.get("rate_percent", raw_rule.get("luxury_tax_percent"))
            )
            if not hs_code or threshold_value is None or rate_percent is None:
                continue
            entries.append(
                {
                    "rule_type": "LUXURY",
                    "hs_code": hs_code,
                    "threshold_value": threshold_value,
                    "rate_percent": rate_percent,
                    "effective_date": effective_date,
                    "notes": notes,
                }
            )

    return entries


def _ranges_overlap(
    min_a: Decimal,
    max_a: Decimal,
    min_b: Decimal,
    max_b: Decimal,
) -> bool:
    return min_a <= max_b and min_b <= max_a


def _format_vehicle_rule_identity(
    *,
    category_code: str | None,
    fuel_type: str,
    hs_code: str,
    power_kw_min: Decimal | None,
    power_kw_max: Decimal | None,
    age_years_min: Decimal | None,
    age_years_max: Decimal | None,
) -> str:
    return (
        f"category={category_code or 'UNKNOWN'}, "
        f"fuel={fuel_type}, "
        f"hs_code={hs_code or 'UNKNOWN'}, "
        f"power={power_kw_min}-{power_kw_max} kW, "
        f"age={age_years_min}-{age_years_max} years"
    )


def _validate_vehicle_tax_rule_uniqueness(entries: list[dict[str, Any]]) -> None:
    vehicle_entries = [entry for entry in entries if entry["rule_type"] == "VEHICLE_TAX"]
    seen_hs_range_keys: set[tuple[str, str, str, str, str, str, str]] = set()
    for index, current in enumerate(vehicle_entries):
        current_category = str(current["category_code"])
        current_fuel = str(current["fuel_type"])
        current_hs_code = str(current["hs_code"])
        current_power_min = _coerce_decimal(current["power_kw_min"])
        current_power_max = _coerce_decimal(current["power_kw_max"])
        current_age_min = _coerce_decimal(current["age_years_min"])
        current_age_max = _coerce_decimal(current["age_years_max"])
        hs_range_key = (
            current_category,
            current_fuel,
            current_hs_code,
            str(current_power_min),
            str(current_power_max),
            str(current_age_min),
            str(current_age_max),
        )
        if hs_range_key in seen_hs_range_keys:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Duplicate vehicle tax rule detected for "
                    f"{current_hs_code} with identical power and age ranges"
                ),
            )
        seen_hs_range_keys.add(hs_range_key)

        for other in vehicle_entries[index + 1 :]:
            if (
                str(other["category_code"]) != current_category
                or str(other["fuel_type"]) != current_fuel
            ):
                continue
            other_power_min = _coerce_decimal(other["power_kw_min"])
            other_power_max = _coerce_decimal(other["power_kw_max"])
            other_age_min = _coerce_decimal(other["age_years_min"])
            other_age_max = _coerce_decimal(other["age_years_max"])
            if (
                str(other["hs_code"]) == current_hs_code
                and other_power_min == current_power_min
                and other_power_max == current_power_max
                and other_age_min == current_age_min
                and other_age_max == current_age_max
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Duplicate vehicle tax rule detected for "
                        f"{current_hs_code} with identical power and age ranges"
                    ),
                )
            if _ranges_overlap(
                current_power_min,
                current_power_max,
                other_power_min,
                other_power_max,
            ) and _ranges_overlap(
                current_age_min,
                current_age_max,
                other_age_min,
                other_age_max,
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Electric vehicle tax rules overlap for "
                        f"{current_category}: "
                        f"{current_power_min}-{current_power_max} kW / "
                        f"{current_age_min}-{current_age_max} years conflicts with "
                        f"{other_power_min}-{other_power_max} kW / "
                        f"{other_age_min}-{other_age_max} years"
                    ),
                )


def _merge_gazette_rules(approved_gazettes: list[Gazette]) -> list[dict[str, Any]]:
    merged: dict[tuple[Any, ...], dict[str, Any]] = {}
    for gazette in approved_gazettes:
        for rule in _extract_normalized_rules(gazette):
            key = (
                str(rule["vehicle_type"]),
                str(rule["fuel_type"]),
                str(rule.get("category_code") or ""),
                int(rule["engine_min"]),
                int(rule["engine_max"]),
                str(rule.get("power_kw_min") or ""),
                str(rule.get("power_kw_max") or ""),
                str(rule.get("age_years_min") or ""),
                str(rule.get("age_years_max") or ""),
            )
            current = merged.get(key)
            if current is None:
                current = {
                    "vehicle_type": rule["vehicle_type"],
                    "fuel_type": rule["fuel_type"],
                    "category_code": rule.get("category_code"),
                    "hs_code": rule.get("hs_code"),
                    "engine_min": rule["engine_min"],
                    "engine_max": rule["engine_max"],
                    "power_kw_min": rule.get("power_kw_min"),
                    "power_kw_max": rule.get("power_kw_max"),
                    "age_years_min": rule.get("age_years_min"),
                    "age_years_max": rule.get("age_years_max"),
                    "customs_percent": None,
                    "surcharge_percent": None,
                    "excise_percent": None,
                    "excise_per_kw_amount": None,
                    "vat_percent": None,
                    "pal_percent": None,
                    "cess_percent": None,
                    "luxury_tax_threshold": None,
                    "luxury_tax_percent": None,
                    "apply_on": None,
                    "effective_date": rule["effective_date"],
                    "notes": None,
                }
                merged[key] = current

            for field in (
                "customs_percent",
                "surcharge_percent",
                "excise_percent",
                "excise_per_kw_amount",
                "vat_percent",
                "pal_percent",
                "cess_percent",
                "luxury_tax_threshold",
                "luxury_tax_percent",
                "apply_on",
            ):
                if rule.get(field) is not None:
                    current[field] = rule[field]
                    current["effective_date"] = rule["effective_date"]

            if rule.get("hs_code"):
                current["hs_code"] = str(rule["hs_code"])
            if rule.get("notes"):
                current["notes"] = str(rule["notes"])

    return list(merged.values())


def _merge_dedicated_rule_entries(approved_gazettes: list[Gazette]) -> list[dict[str, Any]]:
    merged: dict[tuple[Any, ...], dict[str, Any]] = {}
    for gazette in approved_gazettes:
        for entry in _extract_dedicated_rule_entries(gazette):
            rule_type = entry["rule_type"]
            key: tuple[Any, ...]
            if rule_type == "VEHICLE_TAX":
                key = (
                    rule_type,
                    entry["category_code"],
                    entry["fuel_type"],
                    str(entry["power_kw_min"]),
                    str(entry["power_kw_max"]),
                    str(entry["age_years_min"]),
                    str(entry["age_years_max"]),
                    entry["hs_code"],
                )
            elif rule_type == "CUSTOMS":
                key = (rule_type, entry["hs_code"])
            elif rule_type == "SURCHARGE":
                key = (rule_type, entry["applies_to"], entry["name"])
            else:
                key = (rule_type, entry["hs_code"])
            current = dict(entry)
            current["gazette_id"] = gazette.id
            merged[key] = current
    return list(merged.values())


def _build_vehicle_tax_rule_rows(
    *, approved_by: User, merged_rules: list[dict[str, Any]]
) -> list[VehicleTaxRule]:
    rows: list[VehicleTaxRule] = []
    for rule in merged_rules:
        if rule["rule_type"] != "VEHICLE_TAX":
            continue
        rows.append(
            VehicleTaxRule(
                gazette_id=rule["gazette_id"],
                category_code=str(rule["category_code"]),
                fuel_type=str(rule["fuel_type"]),
                hs_code=str(rule["hs_code"]),
                power_kw_min=_coerce_decimal(rule["power_kw_min"]),
                power_kw_max=_coerce_decimal(rule["power_kw_max"]),
                age_years_min=_coerce_decimal(rule["age_years_min"]),
                age_years_max=_coerce_decimal(rule["age_years_max"]),
                excise_type=str(rule["excise_type"]),
                excise_rate=_coerce_decimal(rule["excise_rate"]),
                effective_date=rule["effective_date"],
                approved_by_admin=approved_by.id,
                is_active=True,
                notes=str(rule.get("notes") or "") or None,
            )
        )
    return rows


def _build_customs_rule_rows(
    *, approved_by: User, merged_rules: list[dict[str, Any]]
) -> list[CustomsRule]:
    rows: list[CustomsRule] = []
    for rule in merged_rules:
        if rule["rule_type"] != "CUSTOMS":
            continue
        rows.append(
            CustomsRule(
                gazette_id=rule["gazette_id"],
                hs_code=str(rule["hs_code"]),
                customs_percent=_coerce_decimal(rule.get("customs_percent")),
                vat_percent=_coerce_decimal(rule.get("vat_percent")),
                pal_percent=_coerce_decimal(rule.get("pal_percent")),
                cess_type=str(rule.get("cess_type") or CessType.PERCENT.value),
                cess_value=_coerce_decimal(rule.get("cess_value")),
                effective_date=rule["effective_date"],
                approved_by_admin=approved_by.id,
                is_active=True,
                notes=str(rule.get("notes") or "") or None,
            )
        )
    return rows


def _build_surcharge_rule_rows(
    *, approved_by: User, merged_rules: list[dict[str, Any]]
) -> list[SurchargeRule]:
    rows: list[SurchargeRule] = []
    for rule in merged_rules:
        if rule["rule_type"] != "SURCHARGE":
            continue
        rows.append(
            SurchargeRule(
                gazette_id=rule["gazette_id"],
                name=str(rule.get("name") or "CUSTOMS_SURCHARGE"),
                rate_percent=_coerce_decimal(rule.get("rate_percent")),
                applies_to=str(rule.get("applies_to") or "CUSTOMS_DUTY"),
                effective_date=rule["effective_date"],
                approved_by_admin=approved_by.id,
                is_active=True,
                notes=str(rule.get("notes") or "") or None,
            )
        )
    return rows


def _build_luxury_tax_rule_rows(
    *, approved_by: User, merged_rules: list[dict[str, Any]]
) -> list[LuxuryTaxRule]:
    rows: list[LuxuryTaxRule] = []
    for rule in merged_rules:
        if rule["rule_type"] != "LUXURY":
            continue
        rows.append(
            LuxuryTaxRule(
                gazette_id=rule["gazette_id"],
                hs_code=str(rule["hs_code"]),
                threshold_value=_coerce_decimal(rule["threshold_value"]),
                rate_percent=_coerce_decimal(rule["rate_percent"]),
                effective_date=rule["effective_date"],
                approved_by_admin=approved_by.id,
                is_active=True,
                notes=str(rule.get("notes") or "") or None,
            )
        )
    return rows


def _build_tax_rule_rows(
    *, gazette_id: UUID, approved_by: User, merged_rules: list[dict[str, Any]]
) -> list[TaxRule]:
    rows: list[TaxRule] = []
    for rule in merged_rules:
        rows.append(
            TaxRule(
                gazette_id=gazette_id,
                vehicle_type=str(rule["vehicle_type"]),
                fuel_type=str(rule["fuel_type"]),
                category_code=str(rule.get("category_code") or "") or None,
                hs_code=str(rule.get("hs_code") or "") or None,
                engine_min=int(rule["engine_min"]),
                engine_max=int(rule["engine_max"]),
                power_kw_min=_coerce_optional_decimal(rule.get("power_kw_min")),
                power_kw_max=_coerce_optional_decimal(rule.get("power_kw_max")),
                age_years_min=_coerce_optional_decimal(rule.get("age_years_min")),
                age_years_max=_coerce_optional_decimal(rule.get("age_years_max")),
                customs_percent=_coerce_decimal(rule.get("customs_percent")),
                surcharge_percent=_coerce_decimal(rule.get("surcharge_percent")),
                excise_percent=_coerce_decimal(rule.get("excise_percent")),
                excise_per_kw_amount=_coerce_optional_decimal(rule.get("excise_per_kw_amount")),
                vat_percent=_coerce_decimal(rule.get("vat_percent"), "15"),
                pal_percent=_coerce_decimal(rule.get("pal_percent"), "0"),
                cess_percent=_coerce_decimal(rule.get("cess_percent"), "0"),
                luxury_tax_threshold=_coerce_optional_decimal(rule.get("luxury_tax_threshold")),
                luxury_tax_percent=_coerce_optional_decimal(rule.get("luxury_tax_percent")),
                apply_on=str(rule.get("apply_on") or ApplyOn.CIF.value),
                effective_date=rule["effective_date"],
                approved_by_admin=approved_by.id,
                is_active=True,
                notes=str(rule.get("notes") or "") or None,
            )
        )
    return rows


def _normalize_review_rules(rules: list[GazetteRuleInput]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for rule in rules:
        rule_type = str(rule.rule_type or "").strip().upper() or "VEHICLE_TAX"
        normalized_rule: dict[str, Any] = {
            "rule_type": rule_type,
            "hs_code": str(rule.hs_code or "").strip() or None,
            "engine_min": int(rule.engine_min),
            "engine_max": int(rule.engine_max),
            "power_kw_min": (
                float(_coerce_decimal(rule.power_kw_min))
                if rule.power_kw_min not in (None, "")
                else None
            ),
            "power_kw_max": (
                float(_coerce_decimal(rule.power_kw_max))
                if rule.power_kw_max not in (None, "")
                else None
            ),
            "age_years_min": (
                float(_coerce_decimal(rule.age_years_min))
                if rule.age_years_min not in (None, "")
                else None
            ),
            "age_years_max": (
                float(_coerce_decimal(rule.age_years_max))
                if rule.age_years_max not in (None, "")
                else None
            ),
            "excise_type": str(rule.excise_type or "").strip().upper() or None,
            "excise_rate": (
                float(_coerce_decimal(rule.excise_rate))
                if rule.excise_rate not in (None, "")
                else None
            ),
            "customs_percent": (
                float(_coerce_decimal(rule.customs_percent))
                if rule.customs_percent not in (None, "")
                else None
            ),
            "surcharge_percent": (
                float(_coerce_decimal(rule.surcharge_percent))
                if rule.surcharge_percent not in (None, "")
                else None
            ),
            "excise_percent": (
                float(_coerce_decimal(rule.excise_percent))
                if rule.excise_percent not in (None, "")
                else None
            ),
            "excise_per_kw_amount": (
                float(_coerce_decimal(rule.excise_per_kw_amount))
                if rule.excise_per_kw_amount not in (None, "")
                else None
            ),
            "vat_percent": (
                float(_coerce_decimal(rule.vat_percent, "15"))
                if rule.vat_percent not in (None, "")
                else None
            ),
            "pal_percent": (
                float(_coerce_decimal(rule.pal_percent))
                if rule.pal_percent not in (None, "")
                else None
            ),
            "cess_percent": (
                float(_coerce_decimal(rule.cess_percent))
                if rule.cess_percent not in (None, "")
                else None
            ),
            "cess_type": str(rule.cess_type or "").strip().upper() or None,
            "cess_value": (
                float(_coerce_decimal(rule.cess_value))
                if rule.cess_value not in (None, "")
                else None
            ),
            "luxury_tax_threshold": (
                float(_coerce_decimal(rule.luxury_tax_threshold))
                if rule.luxury_tax_threshold not in (None, "")
                else None
            ),
            "luxury_tax_percent": (
                float(_coerce_decimal(rule.luxury_tax_percent))
                if rule.luxury_tax_percent not in (None, "")
                else None
            ),
            "threshold_value": (
                float(_coerce_decimal(rule.threshold_value))
                if rule.threshold_value not in (None, "")
                else None
            ),
            "rate_percent": (
                float(_coerce_decimal(rule.rate_percent))
                if rule.rate_percent not in (None, "")
                else None
            ),
            "applies_to": str(rule.applies_to or "").strip().upper() or None,
            "name": str(rule.name or "").strip() or None,
            "apply_on": ApplyOn(rule.apply_on.upper()).value,
            "notes": (rule.notes or "").strip() or None,
        }

        if rule_type == "VEHICLE_TAX":
            fuel_type = _normalize_fuel_type(rule.fuel_type)
            vehicle_type, inferred_category_code = _normalize_vehicle_type(
                rule.vehicle_type, fuel_type
            )
            normalized_rule["vehicle_type"] = vehicle_type
            normalized_rule["fuel_type"] = fuel_type
            normalized_rule["category_code"] = (
                _slug_category_code(rule.category_code)
                if rule.category_code
                else inferred_category_code
            )
            canonical_electric_rule = canonicalize_electric_vehicle_rule(normalized_rule)
            if canonical_electric_rule is not None:
                normalized.append(canonical_electric_rule)
                continue
        else:
            normalized_rule["vehicle_type"] = str(rule.vehicle_type or "").strip().upper() or None
            normalized_rule["fuel_type"] = str(rule.fuel_type or "").strip().upper() or None
            normalized_rule["category_code"] = (
                _slug_category_code(rule.category_code) if rule.category_code else None
            )

        normalized.append(normalized_rule)
    return normalized


def _save_gazette_for_manual_review(
    *,
    db: Session,
    current_user: User,
    gazette_no: str,
    extraction: dict[str, Any] | None,
    message: str,
    existing_gazette: Gazette | None = None,
) -> GazetteUploadResponse:
    fallback_payload = _sanitize_extracted_payload(
        {
            "error": message,
            "text": (extraction or {}).get("text", ""),
            "tables": (extraction or {}).get("tables", []),
            "gazette_no": gazette_no,
            "rules": [],
            "effective_date": None,
        }
    )

    if existing_gazette is not None:
        gazette = existing_gazette
        gazette.effective_date = None
        gazette.raw_extracted = fallback_payload
        gazette.status = GazetteStatus.PENDING.value
        gazette.uploaded_by = current_user.id
        gazette.approved_by = None
        gazette.rejection_reason = None
        gazette.updated_at = datetime.utcnow()
    else:
        gazette = Gazette(
            gazette_no=gazette_no,
            effective_date=None,
            raw_extracted=fallback_payload,
            status=GazetteStatus.PENDING.value,
            uploaded_by=current_user.id,
        )
        db.add(gazette)
        db.flush()
    db.add(
        AuditLog(
            event_type=AuditEventType.GAZETTE_UPLOADED,
            user_id=current_user.id,
            admin_id=current_user.id,
            details={
                "gazette_id": str(gazette.id),
                "gazette_no": gazette.gazette_no,
                "rules_count": 0,
                "uploaded_by": current_user.email,
                "message": message,
            },
        )
    )
    db.commit()
    db.refresh(gazette)

    return GazetteUploadResponse(
        gazette_id=str(gazette.id),
        gazette_no=gazette.gazette_no,
        effective_date=None,
        rules_count=0,
        confidence=float((extraction or {}).get("confidence", 0.0)),
        status="NEEDS_MANUAL_REVIEW",
        preview=fallback_payload,
        message=message,
    )


@router.post("/upload", response_model=GazetteUploadResponse)
async def upload_gazette(
    file: UploadFile = File(...),
    gazette_no: str = Form(...),
    current_user: User = Depends(require_permission(Permission.MANAGE_USERS)),
    db: Session = Depends(get_db),
) -> GazetteUploadResponse:
    """Upload a gazette PDF, extract rules, and save for admin review."""
    filename = (file.filename or "").lower()
    if not filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )

    content = await file.read()
    max_size_bytes = settings.MAX_GAZETTE_SIZE_MB * 1024 * 1024
    if len(content) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.MAX_GAZETTE_SIZE_MB}MB",
        )

    existing = db.query(Gazette).filter(Gazette.gazette_no == gazette_no).first()
    if existing and existing.status == GazetteStatus.APPROVED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Gazette {gazette_no} already exists (status: {existing.status})",
        )

    try:
        extraction = await document_ai_service.parse_gazette_pdf(content)
    except Exception as exc:
        logger.warning("Document AI parsing failed for %s: %s", gazette_no, exc)
        return _save_gazette_for_manual_review(
            db=db,
            current_user=current_user,
            gazette_no=gazette_no,
            extraction=None,
            message=f"Automatic PDF extraction failed. Manual review required. {exc}",
            existing_gazette=existing,
        )

    try:
        structured = await gemini_service.structure_gazette(
            raw_text=extraction.get("text", ""),
            tables=extraction.get("tables", []),
            gazette_no=gazette_no,
        )
        fallback_structured = parse_ocr_to_rules(extraction.get("text", ""), gazette_no)
        if fallback_structured and len(fallback_structured.get("rules", [])) > len(
            structured.get("rules", [])
        ):
            structured = fallback_structured
        structured = _sanitize_extracted_payload(structured)
        effective = _parse_effective_date(structured.get("effective_date"))

        if existing is not None:
            gazette = existing
            gazette.effective_date = effective
            gazette.raw_extracted = structured
            gazette.status = GazetteStatus.PENDING.value
            gazette.uploaded_by = current_user.id
            gazette.approved_by = None
            gazette.rejection_reason = None
            gazette.updated_at = datetime.utcnow()
        else:
            gazette = Gazette(
                gazette_no=gazette_no,
                effective_date=effective,
                raw_extracted=structured,
                status=GazetteStatus.PENDING.value,
                uploaded_by=current_user.id,
            )
            db.add(gazette)
            db.flush()
        db.add(
            AuditLog(
                event_type=AuditEventType.GAZETTE_UPLOADED,
                user_id=current_user.id,
                admin_id=current_user.id,
                details={
                    "gazette_id": str(gazette.id),
                    "gazette_no": gazette.gazette_no,
                    "rules_count": len(structured.get("rules", [])),
                    "uploaded_by": current_user.email,
                },
            )
        )
        db.commit()
        db.refresh(gazette)

        return GazetteUploadResponse(
            gazette_id=str(gazette.id),
            gazette_no=gazette.gazette_no,
            effective_date=structured.get("effective_date"),
            rules_count=len(structured.get("rules", [])),
            confidence=float(extraction.get("confidence", 0.0)),
            status=GazetteStatus.PENDING.value,
            preview=structured,
        )
    except Exception as exc:
        logger.warning("Gemini structuring failed for %s: %s", gazette_no, exc)
        fallback_structured = parse_ocr_to_rules(extraction.get("text", ""), gazette_no)
        if fallback_structured and fallback_structured.get("rules"):
            fallback_structured = _sanitize_extracted_payload(fallback_structured)
            effective = _parse_effective_date(fallback_structured.get("effective_date"))

            if existing is not None:
                gazette = existing
                gazette.effective_date = effective
                gazette.raw_extracted = fallback_structured
                gazette.status = GazetteStatus.PENDING.value
                gazette.uploaded_by = current_user.id
                gazette.approved_by = None
                gazette.rejection_reason = None
                gazette.updated_at = datetime.utcnow()
            else:
                gazette = Gazette(
                    gazette_no=gazette_no,
                    effective_date=effective,
                    raw_extracted=fallback_structured,
                    status=GazetteStatus.PENDING.value,
                    uploaded_by=current_user.id,
                )
                db.add(gazette)
                db.flush()
            db.add(
                AuditLog(
                    event_type=AuditEventType.GAZETTE_UPLOADED,
                    user_id=current_user.id,
                    admin_id=current_user.id,
                    details={
                        "gazette_id": str(gazette.id),
                        "gazette_no": gazette.gazette_no,
                        "rules_count": len(fallback_structured.get("rules", [])),
                        "uploaded_by": current_user.email,
                        "message": "Gemini failed; OCR fallback parser used",
                    },
                )
            )
            db.commit()
            db.refresh(gazette)

            return GazetteUploadResponse(
                gazette_id=str(gazette.id),
                gazette_no=gazette.gazette_no,
                effective_date=fallback_structured.get("effective_date"),
                rules_count=len(fallback_structured.get("rules", [])),
                confidence=float(extraction.get("confidence", 0.0)),
                status=GazetteStatus.PENDING.value,
                preview=fallback_structured,
                message="Gemini failed. OCR fallback parser extracted rules for review.",
            )
        return _save_gazette_for_manual_review(
            db=db,
            current_user=current_user,
            gazette_no=gazette_no,
            extraction=extraction,
            message="Automatic extraction failed. Manual review required.",
            existing_gazette=existing,
        )


@router.post("/upload-csv", response_model=GazetteUploadResponse)
async def upload_gazette_csv(
    file: UploadFile = File(...),
    gazette_no: str = Form(...),
    effective_date: str | None = Form(None),
    current_user: User = Depends(require_permission(Permission.MANAGE_USERS)),
    db: Session = Depends(get_db),
) -> GazetteUploadResponse:
    """Upload structured CSV tax rules and save them for admin review."""
    filename = (file.filename or "").lower()
    if not filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported",
        )

    content = await file.read()
    max_size_bytes = settings.MAX_GAZETTE_SIZE_MB * 1024 * 1024
    if len(content) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.MAX_GAZETTE_SIZE_MB}MB",
        )

    existing = db.query(Gazette).filter(Gazette.gazette_no == gazette_no).first()
    if existing and existing.status == GazetteStatus.APPROVED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Gazette {gazette_no} already exists (status: {existing.status})",
        )

    csv_effective_date, rules = _parse_csv_rules(content)
    resolved_effective_date = _parse_effective_date(effective_date) or csv_effective_date
    structured = _json_safe_value(
        _sanitize_extracted_payload(
            {
                "gazette_no": gazette_no,
                "effective_date": (
                    resolved_effective_date.isoformat()
                    if resolved_effective_date is not None
                    else None
                ),
                "rules": rules,
                "text": "",
                "tables": [],
                "source": "CSV_UPLOAD",
            }
        )
    )

    if existing is not None:
        gazette = existing
        gazette.effective_date = resolved_effective_date
        gazette.raw_extracted = structured
        gazette.status = GazetteStatus.PENDING.value
        gazette.uploaded_by = current_user.id
        gazette.approved_by = None
        gazette.rejection_reason = None
        gazette.updated_at = datetime.utcnow()
    else:
        gazette = Gazette(
            gazette_no=gazette_no,
            effective_date=resolved_effective_date,
            raw_extracted=structured,
            status=GazetteStatus.PENDING.value,
            uploaded_by=current_user.id,
        )
        db.add(gazette)
        db.flush()

    db.add(
        AuditLog(
            event_type=AuditEventType.GAZETTE_UPLOADED,
            user_id=current_user.id,
            admin_id=current_user.id,
            details={
                "gazette_id": str(gazette.id),
                "gazette_no": gazette.gazette_no,
                "rules_count": len(structured.get("rules", [])),
                "uploaded_by": current_user.email,
                "source": "CSV_UPLOAD",
                "filename": file.filename,
            },
        )
    )
    db.commit()
    db.refresh(gazette)

    return GazetteUploadResponse(
        gazette_id=str(gazette.id),
        gazette_no=gazette.gazette_no,
        effective_date=structured.get("effective_date"),
        rules_count=len(structured.get("rules", [])),
        confidence=1.0,
        status=GazetteStatus.PENDING.value,
        preview=structured,
        message="CSV uploaded successfully. Review and approve before activation.",
    )


@router.post("/upload-global-tax-parameters-csv", response_model=GazetteUploadResponse)
async def upload_global_tax_parameters_csv(
    file: UploadFile = File(...),
    effective_date: str | None = Form(None),
    current_user: User = Depends(require_permission(Permission.MANAGE_USERS)),
    db: Session = Depends(get_db),
) -> GazetteUploadResponse:
    """Upload the global tax parameters catalog CSV."""
    filename = (file.filename or "").lower()
    if not filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    rows = _parse_global_tax_parameter_rows(await file.read())
    resolved_effective_date = _parse_effective_date(effective_date) or date.today()
    payload = {
        "source": "CATALOG_GLOBAL_TAX_PARAMETERS",
        "dataset": "global_tax_parameters",
        "effective_date": resolved_effective_date.isoformat(),
        "catalog_rows": _json_safe_value(rows),
        "filename": file.filename,
    }
    gazette = Gazette(
        gazette_no=_catalog_gazette_no("GLOBAL_TAX", resolved_effective_date),
        effective_date=resolved_effective_date,
        raw_extracted=payload,
        status=GazetteStatus.PENDING.value,
        uploaded_by=current_user.id,
    )
    db.add(gazette)
    db.flush()
    db.add(
        AuditLog(
            event_type=AuditEventType.GAZETTE_UPLOADED,
            admin_id=current_user.id,
            user_id=current_user.id,
            details={
                "gazette_id": str(gazette.id),
                "gazette_no": gazette.gazette_no,
                "dataset": "global_tax_parameters",
                "uploaded_rows": len(rows),
                "effective_date": resolved_effective_date.isoformat(),
            },
        )
    )
    db.commit()
    db.refresh(gazette)

    return GazetteUploadResponse(
        gazette_id=str(gazette.id),
        gazette_no=gazette.gazette_no,
        effective_date=resolved_effective_date.isoformat(),
        rules_count=len(rows),
        confidence=1.0,
        status=GazetteStatus.PENDING.value,
        preview=payload,
        message="Global tax parameters uploaded for review.",
    )


@router.post("/upload-hs-code-matrix-csv", response_model=GazetteUploadResponse)
async def upload_hs_code_matrix_csv(
    file: UploadFile = File(...),
    effective_date: str | None = Form(None),
    current_user: User = Depends(require_permission(Permission.MANAGE_USERS)),
    db: Session = Depends(get_db),
) -> GazetteUploadResponse:
    """Upload the HS code matrix catalog CSV."""
    filename = (file.filename or "").lower()
    if not filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    rows = _parse_hs_code_matrix_rows(await file.read())
    resolved_effective_date = _parse_effective_date(effective_date) or date.today()
    payload = {
        "source": "CATALOG_HS_CODE_MATRIX",
        "dataset": "hs_code_matrix",
        "effective_date": resolved_effective_date.isoformat(),
        "catalog_rows": _json_safe_value(rows),
        "filename": file.filename,
    }
    gazette = Gazette(
        gazette_no=_catalog_gazette_no("HS_MATRIX", resolved_effective_date),
        effective_date=resolved_effective_date,
        raw_extracted=payload,
        status=GazetteStatus.PENDING.value,
        uploaded_by=current_user.id,
    )
    db.add(gazette)
    db.flush()
    db.add(
        AuditLog(
            event_type=AuditEventType.GAZETTE_UPLOADED,
            admin_id=current_user.id,
            user_id=current_user.id,
            details={
                "gazette_id": str(gazette.id),
                "gazette_no": gazette.gazette_no,
                "dataset": "hs_code_matrix",
                "uploaded_rows": len(rows),
                "effective_date": resolved_effective_date.isoformat(),
            },
        )
    )
    db.commit()
    db.refresh(gazette)

    return GazetteUploadResponse(
        gazette_id=str(gazette.id),
        gazette_no=gazette.gazette_no,
        effective_date=resolved_effective_date.isoformat(),
        rules_count=len(rows),
        confidence=1.0,
        status=GazetteStatus.PENDING.value,
        preview=payload,
        message="HS code matrix uploaded for review.",
    )


@router.patch("/catalog/{dataset}/{record_id}", response_model=dict[str, Any])
async def update_catalog_row(
    dataset: str,
    record_id: str,
    payload: CatalogRowUpdateRequest,
    current_user: User = Depends(require_permission(Permission.MANAGE_USERS)),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    versioning_service = RuleVersioningService(db)
    change_reason = payload.change_reason or "Manual catalog edit"
    parsed_record_id = _parse_gazette_id(record_id)
    values = payload.values

    if dataset == "global_tax_parameters":
        global_record = (
            db.query(GlobalTaxParameter)
            .filter(
                GlobalTaxParameter.id == parsed_record_id, GlobalTaxParameter.is_active.is_(True)
            )
            .first()
        )
        if global_record is None:
            raise HTTPException(status_code=404, detail="Catalog row not found")
        updated_global = versioning_service.update_global_tax_parameter(
            record=global_record,
            parameter_group=str(values.get("parameter_group") or global_record.parameter_group)
            .strip()
            .upper(),
            parameter_name=str(values.get("parameter_name") or global_record.parameter_name)
            .strip()
            .upper(),
            condition_or_type=str(
                values.get("condition_or_type") or global_record.condition_or_type
            )
            .strip()
            .upper(),
            value=_parse_csv_decimal(values.get("value")) or global_record.value,
            unit=str(values.get("unit") or global_record.unit).strip().upper(),
            calculation_order=_parse_int(
                values.get("calculation_order"), global_record.calculation_order
            ),
            applicability_flag=(
                str(values.get("applicability_flag")).strip().upper()
                if values.get("applicability_flag") not in (None, "")
                else global_record.applicability_flag
            ),
            effective_date=_parse_effective_date(values.get("effective_date"))
            or global_record.effective_date,
            changed_by=current_user.id,
            change_reason=change_reason,
        )
        db.commit()
        db.refresh(updated_global)
        return _serialize_catalog_record(updated_global, dataset)

    if dataset == "hs_code_matrix":
        hs_record = (
            db.query(HSCodeMatrixRule)
            .filter(HSCodeMatrixRule.id == parsed_record_id, HSCodeMatrixRule.is_active.is_(True))
            .first()
        )
        if hs_record is None:
            raise HTTPException(status_code=404, detail="Catalog row not found")
        updated_hs = versioning_service.update_hs_code_matrix_rule(
            record=hs_record,
            vehicle_type=str(values.get("vehicle_type") or hs_record.vehicle_type).strip().upper(),
            fuel_type=str(values.get("fuel_type") or hs_record.fuel_type).strip().upper(),
            age_condition=str(values.get("age_condition") or hs_record.age_condition)
            .strip()
            .upper(),
            hs_code=str(values.get("hs_code") or hs_record.hs_code).strip(),
            capacity_min=_parse_csv_decimal(values.get("capacity_min")) or hs_record.capacity_min,
            capacity_max=_parse_csv_decimal(values.get("capacity_max")) or hs_record.capacity_max,
            capacity_unit=str(values.get("capacity_unit") or hs_record.capacity_unit)
            .strip()
            .upper(),
            cid_pct=_parse_csv_decimal(values.get("cid_pct")) or hs_record.cid_pct,
            pal_pct=_parse_csv_decimal(values.get("pal_pct")) or hs_record.pal_pct,
            cess_pct=_parse_csv_decimal(values.get("cess_pct")) or hs_record.cess_pct,
            excise_unit_rate_lkr=(
                _parse_csv_decimal(values.get("excise_unit_rate_lkr"))
                or hs_record.excise_unit_rate_lkr
            ),
            min_excise_flat_rate_lkr=(
                _parse_csv_decimal(values.get("min_excise_flat_rate_lkr"))
                or hs_record.min_excise_flat_rate_lkr
            ),
            effective_date=_parse_effective_date(values.get("effective_date"))
            or hs_record.effective_date,
            changed_by=current_user.id,
            change_reason=change_reason,
        )
        db.commit()
        db.refresh(updated_hs)
        return _serialize_catalog_record(updated_hs, dataset)

    raise HTTPException(status_code=400, detail="Unsupported catalog dataset")


@router.delete("/catalog/{dataset}/{record_id}")
async def delete_catalog_row(
    dataset: str,
    record_id: str,
    change_reason: str | None = None,
    current_user: User = Depends(require_permission(Permission.MANAGE_USERS)),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    versioning_service = RuleVersioningService(db)
    parsed_record_id = _parse_gazette_id(record_id)
    reason = change_reason or "Manual catalog deactivation"

    if dataset == "global_tax_parameters":
        global_record = (
            db.query(GlobalTaxParameter)
            .filter(
                GlobalTaxParameter.id == parsed_record_id, GlobalTaxParameter.is_active.is_(True)
            )
            .first()
        )
        if global_record is None:
            raise HTTPException(status_code=404, detail="Catalog row not found")
        versioning_service.deactivate_global_tax_parameter(
            record=global_record,
            changed_by=current_user.id,
            change_reason=reason,
        )
        db.commit()
        return {"message": "Catalog row deactivated"}

    if dataset == "hs_code_matrix":
        hs_record = (
            db.query(HSCodeMatrixRule)
            .filter(HSCodeMatrixRule.id == parsed_record_id, HSCodeMatrixRule.is_active.is_(True))
            .first()
        )
        if hs_record is None:
            raise HTTPException(status_code=404, detail="Catalog row not found")
        versioning_service.deactivate_hs_code_matrix_rule(
            record=hs_record,
            changed_by=current_user.id,
            change_reason=reason,
        )
        db.commit()
        return {"message": "Catalog row deactivated"}

    raise HTTPException(status_code=400, detail="Unsupported catalog dataset")


@router.get("/history", response_model=GazetteHistoryResponse)
async def list_gazette_history(
    status: str | None = None,
    page: int = 1,
    limit: int = 12,
    current_user: User = Depends(require_permission(Permission.MANAGE_TAX_RULES)),
    db: Session = Depends(get_db),
):
    _ = current_user
    safe_page = max(page, 1)
    safe_limit = min(max(limit, 1), 100)

    query = (
        db.query(Gazette)
        .options(joinedload(Gazette.uploader), joinedload(Gazette.approver))
        .order_by(Gazette.created_at.desc())
    )
    if status:
        query = query.filter(Gazette.status == status)

    total = query.count()
    records = query.offset((safe_page - 1) * safe_limit).limit(safe_limit).all()

    items: list[GazetteHistoryItem] = []
    for record in records:
        payload = _sanitize_extracted_payload(record.raw_extracted or {})
        rules_count = _review_item_count(payload)
        items.append(
            GazetteHistoryItem(
                id=str(record.id),
                gazette_no=record.gazette_no,
                effective_date=(
                    record.effective_date.isoformat() if record.effective_date else None
                ),
                status=record.status,
                rules_count=rules_count,
                created_at=record.created_at,
                uploaded_by=record.uploader.email if record.uploader else None,
                approved_by=record.approver.email if record.approver else None,
                rejection_reason=record.rejection_reason,
            )
        )

    total_pages = max(1, (total + safe_limit - 1) // safe_limit)
    return GazetteHistoryResponse(
        items=items,
        total=total,
        page=safe_page,
        limit=safe_limit,
        total_pages=total_pages,
    )


@router.get("/{gazette_id}", response_model=GazetteDetailResponse)
async def get_gazette_detail(
    gazette_id: str,
    current_user: User = Depends(require_permission(Permission.MANAGE_TAX_RULES)),
    db: Session = Depends(get_db),
):
    _ = current_user
    parsed_gazette_id = _parse_gazette_id(gazette_id)
    gazette = (
        db.query(Gazette)
        .options(joinedload(Gazette.uploader), joinedload(Gazette.approver))
        .filter(Gazette.id == parsed_gazette_id)
        .first()
    )
    if gazette is None:
        raise HTTPException(status_code=404, detail="Gazette not found")

    payload = _sanitize_extracted_payload(gazette.raw_extracted or {})
    rules_count = _review_item_count(payload)
    effective_date = (
        gazette.effective_date.isoformat()
        if gazette.effective_date
        else (str(payload.get("effective_date")) if payload.get("effective_date") else None)
    )

    return GazetteDetailResponse(
        gazette_id=str(gazette.id),
        gazette_no=gazette.gazette_no,
        effective_date=effective_date,
        rules_count=rules_count,
        status=gazette.status,
        preview=payload,
        rejection_reason=gazette.rejection_reason,
        uploaded_by=gazette.uploader.email if gazette.uploader else None,
        approved_by=gazette.approver.email if gazette.approver else None,
        created_at=gazette.created_at,
    )


@router.patch("/{gazette_id}", response_model=GazetteDetailResponse)
async def update_gazette_review(
    gazette_id: str,
    payload: GazetteReviewUpdateRequest,
    current_user: User = Depends(require_permission(Permission.MANAGE_TAX_RULES)),
    db: Session = Depends(get_db),
):
    _ = current_user
    parsed_gazette_id = _parse_gazette_id(gazette_id)
    gazette = (
        db.query(Gazette)
        .options(joinedload(Gazette.uploader), joinedload(Gazette.approver))
        .filter(Gazette.id == parsed_gazette_id)
        .first()
    )
    if gazette is None:
        raise HTTPException(status_code=404, detail="Gazette not found")
    if gazette.status == GazetteStatus.APPROVED.value:
        raise HTTPException(status_code=400, detail="Approved gazettes cannot be edited")

    try:
        effective_date = _parse_effective_date(payload.effective_date)
        normalized_rules = _normalize_review_rules(payload.rules)
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail="Gazette review data contains invalid rule values"
        ) from exc

    raw_payload = _sanitize_extracted_payload(dict(gazette.raw_extracted or {}))
    raw_payload["gazette_no"] = gazette.gazette_no
    raw_payload["effective_date"] = effective_date.isoformat() if effective_date else None
    raw_payload["rules"] = normalized_rules
    raw_payload = _sanitize_extracted_payload(raw_payload)

    gazette.effective_date = effective_date
    gazette.raw_extracted = raw_payload
    gazette.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(gazette)

    return GazetteDetailResponse(
        gazette_id=str(gazette.id),
        gazette_no=gazette.gazette_no,
        effective_date=(gazette.effective_date.isoformat() if gazette.effective_date else None),
        rules_count=len(normalized_rules),
        status=gazette.status,
        preview=raw_payload,
        rejection_reason=gazette.rejection_reason,
        uploaded_by=gazette.uploader.email if gazette.uploader else None,
        approved_by=gazette.approver.email if gazette.approver else None,
        created_at=gazette.created_at,
    )


@router.patch("/{gazette_id}/catalog-review", response_model=GazetteDetailResponse)
async def update_catalog_review(
    gazette_id: str,
    payload: CatalogReviewUpdateRequest,
    current_user: User = Depends(require_permission(Permission.MANAGE_TAX_RULES)),
    db: Session = Depends(get_db),
):
    _ = current_user
    parsed_gazette_id = _parse_gazette_id(gazette_id)
    gazette = (
        db.query(Gazette)
        .options(joinedload(Gazette.uploader), joinedload(Gazette.approver))
        .filter(Gazette.id == parsed_gazette_id)
        .first()
    )
    if gazette is None:
        raise HTTPException(status_code=404, detail="Gazette not found")
    if gazette.status == GazetteStatus.APPROVED.value:
        raise HTTPException(status_code=400, detail="Approved gazettes cannot be edited")

    raw_payload = dict(gazette.raw_extracted or {})
    if not _is_catalog_payload(raw_payload):
        raise HTTPException(status_code=400, detail="Gazette is not a catalog review item")

    effective_date = _parse_effective_date(payload.effective_date) or gazette.effective_date
    raw_payload["effective_date"] = effective_date.isoformat() if effective_date else None
    raw_payload["catalog_rows"] = _json_safe_value(payload.rows)
    raw_payload["change_reason"] = payload.change_reason
    gazette.effective_date = effective_date
    gazette.raw_extracted = raw_payload
    gazette.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(gazette)

    return GazetteDetailResponse(
        gazette_id=str(gazette.id),
        gazette_no=gazette.gazette_no,
        effective_date=(gazette.effective_date.isoformat() if gazette.effective_date else None),
        rules_count=_review_item_count(raw_payload),
        status=gazette.status,
        preview=raw_payload,
        rejection_reason=gazette.rejection_reason,
        uploaded_by=gazette.uploader.email if gazette.uploader else None,
        approved_by=gazette.approver.email if gazette.approver else None,
        created_at=gazette.created_at,
    )


@router.post("/{gazette_id}/approve")
async def approve_gazette(
    gazette_id: str,
    current_user: User = Depends(require_permission(Permission.APPROVE_TAX_RULES)),
    db: Session = Depends(get_db),
):
    parsed_gazette_id = _parse_gazette_id(gazette_id)
    gazette = db.query(Gazette).filter(Gazette.id == parsed_gazette_id).first()
    if gazette is None:
        raise HTTPException(status_code=404, detail="Gazette not found")
    if gazette.status == GazetteStatus.APPROVED.value:
        raise HTTPException(status_code=400, detail="Gazette is already approved")

    payload = dict(gazette.raw_extracted or {})
    if _is_catalog_payload(payload):
        versioning_service = RuleVersioningService(db)
        catalog_rows = _catalog_rows(payload)
        effective_date = (
            _parse_effective_date(payload.get("effective_date"))
            or gazette.effective_date
            or date.today()
        )
        applied_rows = 0
        superseded_rows = 0
        dataset = str(payload.get("dataset") or "")
        if dataset == "hs_code_matrix":
            superseded_rows += versioning_service.supersede_overlapping_hs_code_matrix_rules(
                rows=catalog_rows,
                changed_by=current_user.id,
                change_reason=str(
                    payload.get("change_reason") or f"Approved catalog upload: {gazette.gazette_no}"
                ),
            )
        for row in catalog_rows:
            if dataset == "global_tax_parameters":
                global_record = versioning_service.upsert_global_tax_parameter(
                    parameter_group=str(row["parameter_group"]),
                    parameter_name=str(row["parameter_name"]),
                    condition_or_type=str(row["condition_or_type"]),
                    value=row["value"],
                    unit=str(row["unit"]),
                    calculation_order=int(row["calculation_order"]),
                    applicability_flag=row.get("applicability_flag"),
                    effective_date=effective_date,
                    changed_by=current_user.id,
                    change_reason=str(
                        payload.get("change_reason")
                        or f"Approved catalog upload: {gazette.gazette_no}"
                    ),
                )
                if global_record.version > 1:
                    superseded_rows += 1
            elif dataset == "hs_code_matrix":
                hs_record = versioning_service.upsert_hs_code_matrix_rule(
                    vehicle_type=str(row["vehicle_type"]),
                    fuel_type=str(row["fuel_type"]),
                    age_condition=str(row["age_condition"]),
                    hs_code=str(row["hs_code"]),
                    capacity_min=row["capacity_min"],
                    capacity_max=row["capacity_max"],
                    capacity_unit=str(row["capacity_unit"]),
                    cid_pct=row["cid_pct"],
                    pal_pct=row["pal_pct"],
                    cess_pct=row["cess_pct"],
                    excise_unit_rate_lkr=row["excise_unit_rate_lkr"],
                    min_excise_flat_rate_lkr=row.get("min_excise_flat_rate_lkr", Decimal("0")),
                    effective_date=effective_date,
                    changed_by=current_user.id,
                    change_reason=str(
                        payload.get("change_reason")
                        or f"Approved catalog upload: {gazette.gazette_no}"
                    ),
                )
                if hs_record.version > 1:
                    superseded_rows += 1
            else:
                raise HTTPException(status_code=400, detail="Unsupported catalog dataset")
            applied_rows += 1

        gazette.status = GazetteStatus.APPROVED.value
        gazette.approved_by = current_user.id
        gazette.rejection_reason = None
        db.add(
            AuditLog(
                event_type=AuditEventType.GAZETTE_APPROVED,
                user_id=gazette.uploaded_by,
                admin_id=current_user.id,
                details={
                    "gazette_id": str(gazette.id),
                    "gazette_no": gazette.gazette_no,
                    "approved_by": current_user.email,
                    "dataset": dataset,
                    "rows_applied": applied_rows,
                    "rows_superseded": superseded_rows,
                },
            )
        )
        db.commit()
        return {"message": "Catalog upload approved successfully", "gazette_id": str(gazette.id)}

    gazette.status = GazetteStatus.APPROVED.value
    gazette.approved_by = current_user.id
    gazette.rejection_reason = None
    _ = _extract_dedicated_rule_entries(gazette)
    approved_gazettes = (
        db.query(Gazette)
        .filter(Gazette.status == GazetteStatus.APPROVED.value)
        .order_by(Gazette.effective_date.asc(), Gazette.created_at.asc())
        .all()
    )
    if all(existing.id != gazette.id for existing in approved_gazettes):
        approved_gazettes.append(gazette)
    approved_gazettes.sort(
        key=lambda item: (
            item.effective_date
            or _parse_effective_date((item.raw_extracted or {}).get("effective_date"))
            or date.min,
            item.created_at,
        )
    )
    all_dedicated_entries: list[dict[str, Any]] = []
    for approved_gazette in approved_gazettes:
        all_dedicated_entries.extend(_extract_dedicated_rule_entries(approved_gazette))
    _validate_vehicle_tax_rule_uniqueness(all_dedicated_entries)
    merged_rules = _merge_gazette_rules(approved_gazettes)
    legacy_rules = _build_tax_rule_rows(
        gazette_id=gazette.id,
        approved_by=current_user,
        merged_rules=merged_rules,
    )
    merged_dedicated_rules = _merge_dedicated_rule_entries(approved_gazettes)
    vehicle_tax_rules = _build_vehicle_tax_rule_rows(
        approved_by=current_user,
        merged_rules=merged_dedicated_rules,
    )
    customs_rules = _build_customs_rule_rows(
        approved_by=current_user,
        merged_rules=merged_dedicated_rules,
    )
    surcharge_rules = _build_surcharge_rule_rows(
        approved_by=current_user,
        merged_rules=merged_dedicated_rules,
    )
    luxury_tax_rules = _build_luxury_tax_rule_rows(
        approved_by=current_user,
        merged_rules=merged_dedicated_rules,
    )
    db.query(TaxRule).delete()
    db.query(VehicleTaxRule).delete()
    db.query(CustomsRule).delete()
    db.query(SurchargeRule).delete()
    db.query(LuxuryTaxRule).delete()
    for legacy_rule in legacy_rules:
        db.add(legacy_rule)
    for vehicle_tax_rule in vehicle_tax_rules:
        db.add(vehicle_tax_rule)
    for customs_rule in customs_rules:
        db.add(customs_rule)
    for surcharge_rule in surcharge_rules:
        db.add(surcharge_rule)
    for luxury_tax_rule in luxury_tax_rules:
        db.add(luxury_tax_rule)
    db.add(
        AuditLog(
            event_type=AuditEventType.GAZETTE_APPROVED,
            user_id=gazette.uploaded_by,
            admin_id=current_user.id,
            details={
                "gazette_id": str(gazette.id),
                "gazette_no": gazette.gazette_no,
                "approved_by": current_user.email,
                "rules_count": len(legacy_rules),
                "vehicle_tax_rules_count": len(vehicle_tax_rules),
                "customs_rules_count": len(customs_rules),
                "surcharge_rules_count": len(surcharge_rules),
                "luxury_tax_rules_count": len(luxury_tax_rules),
            },
        )
    )
    db.add(
        AuditLog(
            event_type=AuditEventType.TAX_RULES_ACTIVATED,
            user_id=gazette.uploaded_by,
            admin_id=current_user.id,
            details={
                "gazette_id": str(gazette.id),
                "gazette_no": gazette.gazette_no,
                "rules_activated": len(legacy_rules),
                "vehicle_tax_rules_activated": len(vehicle_tax_rules),
                "customs_rules_activated": len(customs_rules),
                "surcharge_rules_activated": len(surcharge_rules),
                "luxury_tax_rules_activated": len(luxury_tax_rules),
                "effective_date": (
                    gazette.effective_date.isoformat() if gazette.effective_date else None
                ),
            },
        )
    )
    db.commit()
    return {"message": "Gazette approved successfully", "gazette_id": str(gazette.id)}


@router.post("/{gazette_id}/reject")
async def reject_gazette(
    gazette_id: str,
    payload: GazetteDecisionRequest,
    current_user: User = Depends(require_permission(Permission.APPROVE_TAX_RULES)),
    db: Session = Depends(get_db),
):
    parsed_gazette_id = _parse_gazette_id(gazette_id)
    gazette = db.query(Gazette).filter(Gazette.id == parsed_gazette_id).first()
    if gazette is None:
        raise HTTPException(status_code=404, detail="Gazette not found")

    reason = (payload.reason or "").strip()
    if len(reason) < 10:
        raise HTTPException(status_code=400, detail="Reason must be at least 10 characters")

    gazette.status = GazetteStatus.REJECTED.value
    gazette.approved_by = current_user.id
    gazette.rejection_reason = reason
    db.add(
        AuditLog(
            event_type=AuditEventType.GAZETTE_REJECTED,
            user_id=gazette.uploaded_by,
            admin_id=current_user.id,
            details={
                "gazette_id": str(gazette.id),
                "gazette_no": gazette.gazette_no,
                "rejected_by": current_user.email,
                "reason": reason,
            },
        )
    )
    db.commit()
    return {"message": "Gazette rejected successfully", "gazette_id": str(gazette.id)}
