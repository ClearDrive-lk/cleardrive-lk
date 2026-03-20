"""
Deterministic OCR fallback parser for gazette tax rules.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

_DATE_PATTERNS = [
    re.compile(r"\b(\d{4}-\d{2}-\d{2})\b"),
    re.compile(r"\b(\d{2})[./-](\d{2})[./-](\d{4})\b"),
]

_HS_PATTERN = re.compile(r"\b(8703\.80\.\d{2}|8704\.60\.\d{2})\b")
_RATE_PATTERN = re.compile(r"Rs\.?\s*([\d,]+)\s*/?-?\s*per\s*kW", re.IGNORECASE)
_ANY_HS_PATTERN = re.compile(r"\b(\d{4}\.\d{2}\.\d{2})\b")
_PERCENT_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*%")
_THRESHOLD_PATTERN = re.compile(
    r"(?:threshold|exceeding|above|over)\s*(?:rs\.?\s*)?([\d,]+)",
    re.IGNORECASE,
)

_ELECTRIC_HS_RULES: dict[str, dict[str, Any]] = {
    "8703.80.11": {
        "template": {
            "vehicle_type": "OTHER",
            "fuel_type": "ELECTRIC",
            "category_code": "ELECTRIC_AUTO_TRISHAW",
            "power_kw_min": 0.0,
            "power_kw_max": 999999.0,
        },
        "variants": [
            {"rate": 18100.0, "age_years_min": 0.0, "age_years_max": 1.0},
            {"rate": 24100.0, "age_years_min": 1.01, "age_years_max": 2.0},
        ],
    },
    "8703.80.12": {
        "template": {
            "vehicle_type": "OTHER",
            "fuel_type": "ELECTRIC",
            "category_code": "ELECTRIC_AUTO_TRISHAW",
            "power_kw_min": 0.0,
            "power_kw_max": 999999.0,
        },
        "variants": [
            {"rate": 36200.0, "age_years_min": 2.01, "age_years_max": None},
        ],
    },
    "8703.80.21": {
        "template": {
            "vehicle_type": "ELECTRIC",
            "fuel_type": "ELECTRIC",
            "category_code": "PASSENGER_VEHICLE_SOLAR_ELECTRIC",
            "power_kw_min": 0.0,
            "power_kw_max": 999999.0,
        },
        "variants": [
            {"rate": 18100.0, "age_years_min": 0.0, "age_years_max": 1.0},
            {"rate": 36200.0, "age_years_min": 1.01, "age_years_max": 3.0},
        ],
    },
    "8703.80.22": {
        "template": {
            "vehicle_type": "ELECTRIC",
            "fuel_type": "ELECTRIC",
            "category_code": "PASSENGER_VEHICLE_SOLAR_ELECTRIC",
            "power_kw_min": 0.0,
            "power_kw_max": 999999.0,
        },
        "variants": [
            {"rate": 48300.0, "age_years_min": 3.01, "age_years_max": None},
        ],
    },
    "8703.80.31": {
        "template": {
            "vehicle_type": "ELECTRIC",
            "fuel_type": "ELECTRIC",
            "category_code": "PASSENGER_VEHICLE_BEV",
            "power_kw_min": 0.0,
            "power_kw_max": 50.0,
        },
        "variants": [
            {"rate": 18100.0, "age_years_min": 0.0, "age_years_max": 1.0},
            {"rate": 36200.0, "age_years_min": 1.01, "age_years_max": 3.0},
        ],
    },
    "8703.80.32": {
        "template": {
            "vehicle_type": "ELECTRIC",
            "fuel_type": "ELECTRIC",
            "category_code": "PASSENGER_VEHICLE_BEV",
            "power_kw_min": 50.01,
            "power_kw_max": 100.0,
        },
        "variants": [
            {"rate": 24100.0, "age_years_min": 0.0, "age_years_max": 1.0},
            {"rate": 36200.0, "age_years_min": 1.01, "age_years_max": 3.0},
        ],
    },
    "8703.80.33": {
        "template": {
            "vehicle_type": "ELECTRIC",
            "fuel_type": "ELECTRIC",
            "category_code": "PASSENGER_VEHICLE_BEV",
            "power_kw_min": 100.01,
            "power_kw_max": 200.0,
        },
        "variants": [
            {"rate": 36200.0, "age_years_min": 0.0, "age_years_max": 1.0},
            {"rate": 60400.0, "age_years_min": 1.01, "age_years_max": 3.0},
        ],
    },
    "8703.80.34": {
        "template": {
            "vehicle_type": "ELECTRIC",
            "fuel_type": "ELECTRIC",
            "category_code": "PASSENGER_VEHICLE_BEV",
            "power_kw_min": 200.01,
            "power_kw_max": 999999.0,
        },
        "variants": [
            {"rate": 96600.0, "age_years_min": 0.0, "age_years_max": 1.0},
            {"rate": 132800.0, "age_years_min": 1.01, "age_years_max": 3.0},
        ],
    },
    "8703.80.41": {
        "template": {
            "vehicle_type": "ELECTRIC",
            "fuel_type": "ELECTRIC",
            "category_code": "PASSENGER_VEHICLE_BEV",
            "power_kw_min": 0.0,
            "power_kw_max": 50.0,
        },
        "variants": [
            {"rate": 48300.0, "age_years_min": 3.01, "age_years_max": None},
        ],
    },
    "8703.80.42": {
        "template": {
            "vehicle_type": "ELECTRIC",
            "fuel_type": "ELECTRIC",
            "category_code": "PASSENGER_VEHICLE_BEV",
            "power_kw_min": 50.01,
            "power_kw_max": 100.0,
        },
        "variants": [
            {"rate": 72400.0, "age_years_min": 3.01, "age_years_max": None},
        ],
    },
    "8703.80.43": {
        "template": {
            "vehicle_type": "ELECTRIC",
            "fuel_type": "ELECTRIC",
            "category_code": "PASSENGER_VEHICLE_BEV",
            "power_kw_min": 100.01,
            "power_kw_max": 200.0,
        },
        "variants": [
            {"rate": 108700.0, "age_years_min": 3.01, "age_years_max": None},
        ],
    },
    "8703.80.44": {
        "template": {
            "vehicle_type": "ELECTRIC",
            "fuel_type": "ELECTRIC",
            "category_code": "PASSENGER_VEHICLE_BEV",
            "power_kw_min": 200.01,
            "power_kw_max": 999999.0,
        },
        "variants": [
            {"rate": 144900.0, "age_years_min": 3.01, "age_years_max": None},
        ],
    },
    "8703.80.51": {
        "template": {
            "vehicle_type": "ELECTRIC",
            "fuel_type": "ELECTRIC",
            "category_code": "PASSENGER_VEHICLE_RANGE_EXTENDED_EV",
            "power_kw_min": 0.0,
            "power_kw_max": 50.0,
        },
        "variants": [
            {"rate": 18100.0, "age_years_min": 0.0, "age_years_max": 1.0},
            {"rate": 36200.0, "age_years_min": 1.01, "age_years_max": 3.0},
        ],
    },
    "8703.80.52": {
        "template": {
            "vehicle_type": "ELECTRIC",
            "fuel_type": "ELECTRIC",
            "category_code": "PASSENGER_VEHICLE_RANGE_EXTENDED_EV",
            "power_kw_min": 50.01,
            "power_kw_max": 100.0,
        },
        "variants": [
            {"rate": 24100.0, "age_years_min": 0.0, "age_years_max": 1.0},
            {"rate": 36200.0, "age_years_min": 1.01, "age_years_max": 3.0},
        ],
    },
    "8703.80.53": {
        "template": {
            "vehicle_type": "ELECTRIC",
            "fuel_type": "ELECTRIC",
            "category_code": "PASSENGER_VEHICLE_RANGE_EXTENDED_EV",
            "power_kw_min": 100.01,
            "power_kw_max": 200.0,
        },
        "variants": [
            {"rate": 36200.0, "age_years_min": 0.0, "age_years_max": 1.0},
            {"rate": 60400.0, "age_years_min": 1.01, "age_years_max": 3.0},
        ],
    },
    "8703.80.54": {
        "template": {
            "vehicle_type": "ELECTRIC",
            "fuel_type": "ELECTRIC",
            "category_code": "PASSENGER_VEHICLE_RANGE_EXTENDED_EV",
            "power_kw_min": 200.01,
            "power_kw_max": 999999.0,
        },
        "variants": [
            {"rate": 96600.0, "age_years_min": 0.0, "age_years_max": 1.0},
            {"rate": 132800.0, "age_years_min": 1.01, "age_years_max": 3.0},
        ],
    },
    "8703.80.61": {
        "template": {
            "vehicle_type": "ELECTRIC",
            "fuel_type": "ELECTRIC",
            "category_code": "PASSENGER_VEHICLE_RANGE_EXTENDED_EV",
            "power_kw_min": 0.0,
            "power_kw_max": 50.0,
        },
        "variants": [
            {"rate": 48300.0, "age_years_min": 3.01, "age_years_max": None},
        ],
    },
    "8703.80.62": {
        "template": {
            "vehicle_type": "ELECTRIC",
            "fuel_type": "ELECTRIC",
            "category_code": "PASSENGER_VEHICLE_RANGE_EXTENDED_EV",
            "power_kw_min": 50.01,
            "power_kw_max": 100.0,
        },
        "variants": [
            {"rate": 72400.0, "age_years_min": 3.01, "age_years_max": None},
        ],
    },
    "8703.80.63": {
        "template": {
            "vehicle_type": "ELECTRIC",
            "fuel_type": "ELECTRIC",
            "category_code": "PASSENGER_VEHICLE_RANGE_EXTENDED_EV",
            "power_kw_min": 100.01,
            "power_kw_max": 200.0,
        },
        "variants": [
            {"rate": 108700.0, "age_years_min": 3.01, "age_years_max": None},
        ],
    },
    "8703.80.64": {
        "template": {
            "vehicle_type": "ELECTRIC",
            "fuel_type": "ELECTRIC",
            "category_code": "PASSENGER_VEHICLE_RANGE_EXTENDED_EV",
            "power_kw_min": 200.01,
            "power_kw_max": 999999.0,
        },
        "variants": [
            {"rate": 144900.0, "age_years_min": 3.01, "age_years_max": None},
        ],
    },
    "8703.80.71": {
        "template": {
            "vehicle_type": "ELECTRIC",
            "fuel_type": "ELECTRIC",
            "category_code": "PASSENGER_VEHICLE_ELECTRIC_OTHER",
            "power_kw_min": 0.0,
            "power_kw_max": 999999.0,
        },
        "variants": [
            {"rate": 96600.0, "age_years_min": 0.0, "age_years_max": 1.0},
            {"rate": 132800.0, "age_years_min": 1.01, "age_years_max": 3.0},
        ],
    },
    "8703.80.72": {
        "template": {
            "vehicle_type": "ELECTRIC",
            "fuel_type": "ELECTRIC",
            "category_code": "PASSENGER_VEHICLE_ELECTRIC_OTHER",
            "power_kw_min": 0.0,
            "power_kw_max": 999999.0,
        },
        "variants": [
            {"rate": 144900.0, "age_years_min": 3.01, "age_years_max": None},
        ],
    },
    "8704.60.10": {
        "template": {
            "vehicle_type": "TRUCK",
            "fuel_type": "ELECTRIC",
            "category_code": "ELECTRIC_AUTO_TRISHAW_GOODS",
            "power_kw_min": 0.0,
            "power_kw_max": 999999.0,
        },
        "variants": [
            {"rate": 18100.0, "age_years_min": 0.0, "age_years_max": 5.0},
        ],
    },
    "8704.60.20": {
        "template": {
            "vehicle_type": "TRUCK",
            "fuel_type": "ELECTRIC",
            "category_code": "ELECTRIC_AUTO_TRISHAW_GOODS",
            "power_kw_min": 0.0,
            "power_kw_max": 999999.0,
        },
        "variants": [
            {"rate": 18100.0, "age_years_min": 5.01, "age_years_max": None},
        ],
    },
    "8704.60.31": {
        "template": {
            "vehicle_type": "TRUCK",
            "fuel_type": "ELECTRIC",
            "category_code": "GOODS_VEHICLE_ELECTRIC",
            "power_kw_min": 0.0,
            "power_kw_max": 50.0,
        },
        "variants": [
            {"rate": 18100.0, "age_years_min": 0.0, "age_years_max": 5.0},
        ],
    },
    "8704.60.32": {
        "template": {
            "vehicle_type": "TRUCK",
            "fuel_type": "ELECTRIC",
            "category_code": "GOODS_VEHICLE_ELECTRIC",
            "power_kw_min": 50.01,
            "power_kw_max": 100.0,
        },
        "variants": [
            {"rate": 24100.0, "age_years_min": 0.0, "age_years_max": 5.0},
        ],
    },
    "8704.60.33": {
        "template": {
            "vehicle_type": "TRUCK",
            "fuel_type": "ELECTRIC",
            "category_code": "GOODS_VEHICLE_ELECTRIC",
            "power_kw_min": 100.01,
            "power_kw_max": 200.0,
        },
        "variants": [
            {"rate": 60400.0, "age_years_min": 0.0, "age_years_max": 5.0},
        ],
    },
    "8704.60.34": {
        "template": {
            "vehicle_type": "TRUCK",
            "fuel_type": "ELECTRIC",
            "category_code": "GOODS_VEHICLE_ELECTRIC",
            "power_kw_min": 200.01,
            "power_kw_max": 999999.0,
        },
        "variants": [
            {"rate": 96600.0, "age_years_min": 0.0, "age_years_max": 5.0},
        ],
    },
    "8704.60.41": {
        "template": {
            "vehicle_type": "TRUCK",
            "fuel_type": "ELECTRIC",
            "category_code": "GOODS_VEHICLE_ELECTRIC",
            "power_kw_min": 0.0,
            "power_kw_max": 50.0,
        },
        "variants": [
            {"rate": 48300.0, "age_years_min": 5.01, "age_years_max": None},
        ],
    },
    "8704.60.42": {
        "template": {
            "vehicle_type": "TRUCK",
            "fuel_type": "ELECTRIC",
            "category_code": "GOODS_VEHICLE_ELECTRIC",
            "power_kw_min": 50.01,
            "power_kw_max": 100.0,
        },
        "variants": [
            {"rate": 72400.0, "age_years_min": 5.01, "age_years_max": None},
        ],
    },
    "8704.60.43": {
        "template": {
            "vehicle_type": "TRUCK",
            "fuel_type": "ELECTRIC",
            "category_code": "GOODS_VEHICLE_ELECTRIC",
            "power_kw_min": 100.01,
            "power_kw_max": 200.0,
        },
        "variants": [
            {"rate": 108700.0, "age_years_min": 5.01, "age_years_max": None},
        ],
    },
    "8704.60.44": {
        "template": {
            "vehicle_type": "TRUCK",
            "fuel_type": "ELECTRIC",
            "category_code": "GOODS_VEHICLE_ELECTRIC",
            "power_kw_min": 200.01,
            "power_kw_max": 999999.0,
        },
        "variants": [
            {"rate": 144900.0, "age_years_min": 5.01, "age_years_max": None},
        ],
    },
}


def _parse_effective_date(text: str) -> str | None:
    for pattern in _DATE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        if len(match.groups()) == 1:
            return match.group(1)
        day, month, year = match.groups()
        return f"{year}-{month}-{day}"
    return None


def _extract_hs_blocks(raw_text: str) -> list[tuple[str, str]]:
    matches = list(_HS_PATTERN.finditer(raw_text))
    if not matches:
        return []

    blocks: list[tuple[str, str]] = []
    seen_hs_codes: set[str] = set()
    for index, match in enumerate(matches):
        hs_code = match.group(1)
        if hs_code in seen_hs_codes:
            continue
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(raw_text)
        blocks.append((hs_code, raw_text[start:end]))
        seen_hs_codes.add(hs_code)
    return blocks


def _block_contains_expected_rate(block: str, expected_rate: float) -> bool:
    expected_digits = str(int(expected_rate))
    normalized = block.replace(",", "")
    if expected_digits in normalized:
        return True
    found_rates = {match.group(1).replace(",", "") for match in _RATE_PATTERN.finditer(block)}
    return expected_digits in found_rates


def _build_rule(
    hs_code: str, template: dict[str, Any], variant: dict[str, Any], block: str
) -> dict[str, Any]:
    return {
        "category_code": template["category_code"],
        "fuel_type": template["fuel_type"],
        "power_min_kw": template["power_kw_min"],
        "power_max_kw": template["power_kw_max"],
        "age_min_years": variant["age_years_min"],
        "age_max_years": 999.0 if variant["age_years_max"] is None else variant["age_years_max"],
        "hs_code": hs_code,
        "excise_type": "PER_KW",
        "excise_rate": variant["rate"],
    }


def _canonical_rule_matches(
    candidate: dict[str, Any],
    *,
    category_code: str,
    power_min_kw: float,
    power_max_kw: float,
    age_min_years: float,
    age_max_years: float,
) -> bool:
    return (
        candidate["category_code"] == category_code
        and candidate["power_min_kw"] == power_min_kw
        and candidate["power_max_kw"] == power_max_kw
        and candidate["age_min_years"] == age_min_years
        and candidate["age_max_years"] == age_max_years
    )


def _canonicalize_numeric(value: Any, *, open_ended_default: float | None = None) -> float | None:
    if value in (None, ""):
        return open_ended_default
    return float(value)


def _first_present(mapping: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping and mapping[key] not in (None, ""):
            return mapping[key]
    return None


def canonicalize_electric_vehicle_rule(raw_rule: Mapping[str, Any]) -> dict[str, Any] | None:
    fuel_type = str(raw_rule.get("fuel_type") or "").strip().upper()
    category_code = str(raw_rule.get("category_code") or "").strip().upper()
    power_min_kw = _canonicalize_numeric(_first_present(raw_rule, "power_min_kw", "power_kw_min"))
    power_max_kw = _canonicalize_numeric(
        _first_present(raw_rule, "power_max_kw", "power_kw_max"),
        open_ended_default=999999.0,
    )
    age_min_years = _canonicalize_numeric(
        _first_present(raw_rule, "age_min_years", "age_years_min")
    )
    age_max_years = _canonicalize_numeric(
        _first_present(raw_rule, "age_max_years", "age_years_max"),
        open_ended_default=999.0,
    )
    excise_type = str(raw_rule.get("excise_type") or "").strip().upper() or "PER_KW"
    excise_rate = _canonicalize_numeric(
        _first_present(raw_rule, "excise_rate", "excise_per_kw_amount")
    )
    provided_hs_code = str(raw_rule.get("hs_code") or "").strip()

    if (
        fuel_type != "ELECTRIC"
        or not category_code
        or power_min_kw is None
        or power_max_kw is None
        or age_min_years is None
        or age_max_years is None
        or excise_rate is None
    ):
        return None

    candidates: list[dict[str, Any]] = []
    for hs_code, hs_definition in _ELECTRIC_HS_RULES.items():
        template = dict(hs_definition["template"])
        for variant in hs_definition["variants"]:
            candidate = _build_rule(hs_code, template, variant, "")
            if not _canonical_rule_matches(
                candidate,
                category_code=category_code,
                power_min_kw=power_min_kw,
                power_max_kw=power_max_kw,
                age_min_years=age_min_years,
                age_max_years=age_max_years,
            ):
                continue
            if candidate["excise_rate"] != excise_rate:
                continue
            candidates.append(candidate)

    if provided_hs_code:
        matched_hs_candidates = [
            candidate for candidate in candidates if candidate["hs_code"] == provided_hs_code
        ]
        if matched_hs_candidates:
            return matched_hs_candidates[0]

    if len(candidates) == 1:
        return candidates[0]

    if provided_hs_code:
        return {
            "category_code": category_code,
            "fuel_type": fuel_type,
            "power_min_kw": power_min_kw,
            "power_max_kw": power_max_kw,
            "age_min_years": age_min_years,
            "age_max_years": age_max_years,
            "excise_type": excise_type,
            "excise_rate": excise_rate,
            "hs_code": provided_hs_code,
        }

    return None


def _parse_electric_rules(raw_text: str) -> list[dict[str, Any]]:
    if "8703.80." not in raw_text and "8704.60." not in raw_text:
        return []

    rules: list[dict[str, Any]] = []
    for hs_code, block in _extract_hs_blocks(raw_text):
        hs_definition = _ELECTRIC_HS_RULES.get(hs_code)
        if hs_definition is None:
            continue

        template = dict(hs_definition["template"])
        variants = hs_definition["variants"]
        for variant in variants:
            if not _block_contains_expected_rate(block, variant["rate"]):
                continue
            rules.append(_build_rule(hs_code, template, variant, block))

    return rules


def _rule_identity(rule: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(rule.get("category_code") or ""),
        str(rule.get("power_min_kw") or ""),
        str(rule.get("power_max_kw") or ""),
        str(rule.get("age_min_years") or ""),
        str(rule.get("age_max_years") or ""),
    )


def sanitize_electric_vehicle_rules(
    raw_rules: list[dict[str, Any]] | None, raw_text: str = ""
) -> list[dict[str, Any]] | None:
    if not raw_rules:
        return None

    canonical_rules = _parse_electric_rules(raw_text)
    if canonical_rules:
        return canonical_rules

    explicit_canonical_rules = [
        canonical_rule
        for rule in raw_rules
        if isinstance(rule, dict)
        for canonical_rule in [canonicalize_electric_vehicle_rule(rule)]
        if canonical_rule is not None
    ]
    if explicit_canonical_rules:
        return explicit_canonical_rules

    detected_hs_codes: list[str] = []
    seen_hs_codes: set[str] = set()

    for raw_rule in raw_rules:
        if not isinstance(raw_rule, dict):
            continue
        notes = str(raw_rule.get("notes") or "")
        hs_match = _HS_PATTERN.search(notes) or _HS_PATTERN.search(
            str(raw_rule.get("hs_code") or "")
        )
        if hs_match is None:
            continue
        hs_code = hs_match.group(1)
        if hs_code in seen_hs_codes or hs_code not in _ELECTRIC_HS_RULES:
            continue
        detected_hs_codes.append(hs_code)
        seen_hs_codes.add(hs_code)

    if not detected_hs_codes:
        return None

    sanitized_rules: list[dict[str, Any]] = []
    for hs_code in detected_hs_codes:
        hs_definition = _ELECTRIC_HS_RULES[hs_code]
        template = dict(hs_definition["template"])
        notes = f"HS Code: {hs_code}."
        for variant in hs_definition["variants"]:
            sanitized_rules.append(_build_rule(hs_code, template, variant, notes))

    deduped: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    for rule in sanitized_rules:
        deduped[_rule_identity(rule)] = rule
    return list(deduped.values())


def _extract_generic_hs_blocks(raw_text: str) -> list[tuple[str, str]]:
    matches = list(_ANY_HS_PATTERN.finditer(raw_text))
    if not matches:
        return []
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(raw_text)
        blocks.append((match.group(1), raw_text[start:end]))
    return blocks


def _parse_customs_rules(raw_text: str) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    for hs_code, block in _extract_generic_hs_blocks(raw_text):
        upper = block.upper()
        if (
            "CUSTOMS" not in upper
            and "VAT" not in upper
            and "PAL" not in upper
            and "CESS" not in upper
        ):
            continue

        customs_match = re.search(
            r"CUSTOMS(?:\s+DUTY)?[^0-9]{0,20}(\d+(?:\.\d+)?)\s*%", block, re.IGNORECASE
        )
        vat_match = re.search(r"VAT[^0-9]{0,20}(\d+(?:\.\d+)?)\s*%", block, re.IGNORECASE)
        pal_match = re.search(r"PAL[^0-9]{0,20}(\d+(?:\.\d+)?)\s*%", block, re.IGNORECASE)
        cess_percent_match = re.search(r"CESS[^0-9]{0,20}(\d+(?:\.\d+)?)\s*%", block, re.IGNORECASE)
        cess_fixed_match = re.search(r"CESS[^R]{0,20}RS\.?\s*([\d,]+)", block, re.IGNORECASE)

        if not any((customs_match, vat_match, pal_match, cess_percent_match, cess_fixed_match)):
            continue

        if cess_fixed_match:
            cess_type = "FIXED"
            cess_value = float(cess_fixed_match.group(1).replace(",", ""))
        else:
            cess_type = "PERCENT"
            cess_value = float(cess_percent_match.group(1)) if cess_percent_match else 0.0

        rules.append(
            {
                "rule_type": "CUSTOMS",
                "hs_code": hs_code,
                "customs_percent": float(customs_match.group(1)) if customs_match else 0.0,
                "vat_percent": float(vat_match.group(1)) if vat_match else 0.0,
                "pal_percent": float(pal_match.group(1)) if pal_match else 0.0,
                "cess_type": cess_type,
                "cess_value": cess_value,
                "notes": f"HS Code: {hs_code}. {' '.join(block.split())[:180]}",
            }
        )
    return rules


def _parse_surcharge_rules(raw_text: str) -> list[dict[str, Any]]:
    if "SURCHARGE" not in raw_text.upper():
        return []
    match = re.search(
        r"SURCHARGE(?:\s+ON\s+CUSTOMS(?:\s+DUTY)?)?[^0-9]{0,30}(\d+(?:\.\d+)?)\s*%",
        raw_text,
        re.IGNORECASE,
    )
    if not match:
        return []
    return [
        {
            "rule_type": "SURCHARGE",
            "name": "CUSTOMS_SURCHARGE",
            "rate_percent": float(match.group(1)),
            "applies_to": "CUSTOMS_DUTY",
            "notes": "Global customs surcharge extracted from OCR fallback parser.",
        }
    ]


def _parse_luxury_tax_rules(raw_text: str) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    for hs_code, block in _extract_generic_hs_blocks(raw_text):
        upper = block.upper()
        if "LUXURY" not in upper and "THRESHOLD" not in upper:
            continue
        threshold_match = _THRESHOLD_PATTERN.search(block)
        rate_match = re.search(
            r"(?:LUXURY|RATE|TAX)[^0-9]{0,20}(\d+(?:\.\d+)?)\s*%", block, re.IGNORECASE
        )
        if not threshold_match or not rate_match:
            continue
        rules.append(
            {
                "rule_type": "LUXURY",
                "hs_code": hs_code,
                "threshold_value": float(threshold_match.group(1).replace(",", "")),
                "rate_percent": float(rate_match.group(1)),
                "notes": f"HS Code: {hs_code}. {' '.join(block.split())[:180]}",
            }
        )
    return rules


def parse_ocr_to_rules(raw_text: str, gazette_no: str) -> dict[str, Any] | None:
    text = raw_text or ""
    rules = []
    rules.extend(_parse_electric_rules(text))
    rules.extend(_parse_customs_rules(text))
    rules.extend(_parse_surcharge_rules(text))
    rules.extend(_parse_luxury_tax_rules(text))
    if not rules:
        return None

    return {
        "gazette_no": gazette_no,
        "effective_date": _parse_effective_date(text),
        "rules": rules,
    }
