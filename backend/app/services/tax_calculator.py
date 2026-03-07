"""
Tax calculator service for vehicle import duties.

Pure Python deterministic calculation logic backed by DB tax rules.
Story: CD-22
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from app.models.gazette import ApplyOn, TaxFuelType, TaxRule, TaxVehicleType
from sqlalchemy.orm import Session, joinedload

logger = logging.getLogger(__name__)


class NoTaxRuleError(Exception):
    """Raised when no active tax rule matches the requested configuration."""


class TaxCalculator:
    """Service for calculating vehicle import duties from active tax rules."""

    def __init__(self, db: Session):
        self.db = db

    def calculate_import_duty(
        self, vehicle_type: str, fuel_type: str, engine_cc: int, cif_value: float
    ) -> dict[str, Any]:
        self._validate_inputs(vehicle_type, fuel_type, engine_cc, cif_value)

        rule = self._find_matching_rule(vehicle_type, fuel_type, engine_cc)
        if not rule:
            raise NoTaxRuleError(
                f"No active tax rule found for {vehicle_type} {fuel_type} {engine_cc}cc"
            )

        result = self._calculate_duties(Decimal(str(cif_value)), rule)
        result["rule_used"] = {
            "rule_id": str(rule.id),
            "gazette_no": rule.gazette.gazette_no if rule.gazette else "Unknown",
            "effective_date": rule.effective_date.isoformat(),
            "customs_percent": float(rule.customs_percent),
            "excise_percent": float(rule.excise_percent),
            "vat_percent": float(rule.vat_percent),
            "pal_percent": float(rule.pal_percent),
            "cess_percent": float(rule.cess_percent),
            "apply_on": rule.apply_on,
        }
        return result

    def _validate_inputs(
        self, vehicle_type: str, fuel_type: str, engine_cc: int, cif_value: float
    ) -> None:
        valid_vehicle_types = {v.value for v in TaxVehicleType}
        if vehicle_type not in valid_vehicle_types:
            raise ValueError(
                f"Invalid vehicle_type: {vehicle_type}. Valid: {sorted(valid_vehicle_types)}"
            )

        valid_fuel_types = {f.value for f in TaxFuelType}
        if fuel_type not in valid_fuel_types:
            raise ValueError(f"Invalid fuel_type: {fuel_type}. Valid: {sorted(valid_fuel_types)}")

        if engine_cc < 0 or engine_cc > 10000:
            raise ValueError(f"Invalid engine_cc: {engine_cc}. Must be 0-10000")

        if cif_value <= 0:
            raise ValueError(f"Invalid cif_value: {cif_value}. Must be positive")

    def _find_matching_rule(
        self, vehicle_type: str, fuel_type: str, engine_cc: int
    ) -> TaxRule | None:
        return (
            self.db.query(TaxRule)
            .options(joinedload(TaxRule.gazette))
            .filter(
                TaxRule.vehicle_type == vehicle_type,
                TaxRule.fuel_type == fuel_type,
                TaxRule.engine_min <= engine_cc,
                TaxRule.engine_max >= engine_cc,
                TaxRule.is_active.is_(True),
            )
            .order_by(TaxRule.effective_date.desc())
            .first()
        )

    def _calculate_duties(self, cif: Decimal, rule: TaxRule) -> dict[str, Any]:
        customs_rate = Decimal(str(rule.customs_percent)) / Decimal("100")
        excise_rate = Decimal(str(rule.excise_percent)) / Decimal("100")
        cess_rate = Decimal(str(rule.cess_percent)) / Decimal("100")
        vat_rate = Decimal(str(rule.vat_percent)) / Decimal("100")
        pal_rate = Decimal(str(rule.pal_percent)) / Decimal("100")

        customs = cif * customs_rate

        apply_on = rule.apply_on
        if apply_on == ApplyOn.CUSTOMS_ONLY.value:
            base_for_excise = customs
        else:
            # CIF and CIF_PLUS_CUSTOMS and CIF_PLUS_EXCISE start from CIF+customs
            base_for_excise = cif + customs

        excise = base_for_excise * excise_rate
        cess = base_for_excise * cess_rate

        if apply_on == ApplyOn.CIF_PLUS_EXCISE.value:
            taxable_value = cif + customs + excise + cess
        else:
            taxable_value = base_for_excise + excise + cess

        vat = taxable_value * vat_rate
        pal = taxable_value * pal_rate

        total_duty = customs + excise + cess + vat + pal
        total_landed_cost = cif + total_duty
        effective_rate = (total_duty / cif * Decimal("100")) if cif > 0 else Decimal("0")

        return {
            "cif_value": float(cif),
            "customs_duty": float(customs),
            "excise_duty": float(excise),
            "cess": float(cess),
            "vat": float(vat),
            "pal": float(pal),
            "total_duty": float(total_duty),
            "total_landed_cost": float(total_landed_cost),
            "effective_rate_percent": float(effective_rate),
        }


def calculate_tax(
    db: Session, vehicle_type: str, fuel_type: str, engine_cc: int, cif_value: float
) -> dict[str, Any]:
    """Convenience wrapper for tax calculation."""
    calculator = TaxCalculator(db)
    result = calculator.calculate_import_duty(vehicle_type, fuel_type, engine_cc, cif_value)
    logger.info(
        "Tax calculated: %s %s %scc CIF=%s total_duty=%s",
        vehicle_type,
        fuel_type,
        engine_cc,
        cif_value,
        result["total_duty"],
    )
    return result
