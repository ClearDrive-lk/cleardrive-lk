"""
Tax calculator service for vehicle import duties.

Pure Python deterministic calculation logic backed by DB tax rules.
Story: CD-22
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from app.models.gazette import (
    ApplyOn,
    CessType,
    CustomsRule,
    LuxuryTaxRule,
    SurchargeRule,
    TaxFuelType,
    TaxRule,
    TaxVehicleType,
    VehicleTaxRule,
)
from sqlalchemy.orm import Session, joinedload

logger = logging.getLogger(__name__)


class NoTaxRuleError(Exception):
    """Raised when no active tax rule matches the requested configuration."""


class InsufficientVehicleDataError(Exception):
    """Raised when a matching rule exists but required vehicle data is missing."""


class TaxCalculator:
    """Service for calculating vehicle import duties from active tax rules."""

    def __init__(self, db: Session):
        self.db = db

    def calculate_import_duty(
        self,
        vehicle_type: str,
        fuel_type: str,
        engine_cc: int,
        cif_value: float,
        *,
        power_kw: float | None = None,
        vehicle_age_years: float | None = None,
        category_codes: list[str] | None = None,
    ) -> dict[str, Any]:
        self._validate_inputs(
            vehicle_type,
            fuel_type,
            engine_cc,
            cif_value,
            power_kw=power_kw,
            vehicle_age_years=vehicle_age_years,
        )

        dedicated_result = self._calculate_with_dedicated_rules(
            cif_value=cif_value,
            fuel_type=fuel_type,
            power_kw=power_kw,
            vehicle_age_years=vehicle_age_years,
            category_codes=category_codes,
        )
        if dedicated_result is not None:
            return dedicated_result

        rule = self._find_matching_rule(
            vehicle_type,
            fuel_type,
            engine_cc,
            power_kw=power_kw,
            vehicle_age_years=vehicle_age_years,
            category_codes=category_codes,
        )
        if not rule:
            raise NoTaxRuleError(
                f"No active tax rule found for {vehicle_type} {fuel_type} {engine_cc}cc"
            )

        result = self._calculate_duties(Decimal(str(cif_value)), rule, power_kw=power_kw)
        result["rule_used"] = {
            "rule_id": str(rule.id),
            "gazette_no": rule.gazette.gazette_no if rule.gazette else "Unknown",
            "effective_date": rule.effective_date.isoformat(),
            "category_code": rule.category_code,
            "hs_code": rule.hs_code,
            "engine_min": rule.engine_min,
            "engine_max": rule.engine_max,
            "power_kw_min": float(rule.power_kw_min) if rule.power_kw_min is not None else None,
            "power_kw_max": float(rule.power_kw_max) if rule.power_kw_max is not None else None,
            "age_years_min": (
                float(rule.age_years_min) if rule.age_years_min is not None else None
            ),
            "age_years_max": (
                float(rule.age_years_max) if rule.age_years_max is not None else None
            ),
            "customs_percent": float(rule.customs_percent),
            "surcharge_percent": float(rule.surcharge_percent),
            "excise_percent": float(rule.excise_percent),
            "excise_per_kw_amount": (
                float(rule.excise_per_kw_amount) if rule.excise_per_kw_amount is not None else None
            ),
            "vat_percent": float(rule.vat_percent),
            "pal_percent": float(rule.pal_percent),
            "cess_percent": float(rule.cess_percent),
            "luxury_tax_threshold": (
                float(rule.luxury_tax_threshold) if rule.luxury_tax_threshold is not None else None
            ),
            "luxury_tax_percent": (
                float(rule.luxury_tax_percent) if rule.luxury_tax_percent is not None else None
            ),
            "apply_on": rule.apply_on,
            "rule_source": "LEGACY_TAX_RULE",
        }
        return result

    def _calculate_with_dedicated_rules(
        self,
        *,
        cif_value: float,
        fuel_type: str,
        power_kw: float | None,
        vehicle_age_years: float | None,
        category_codes: list[str] | None,
    ) -> dict[str, Any] | None:
        active_vehicle_rule_count = (
            self.db.query(VehicleTaxRule).filter(VehicleTaxRule.is_active.is_(True)).count()
        )
        if active_vehicle_rule_count == 0:
            return None

        if not category_codes:
            raise InsufficientVehicleDataError(
                "Vehicle category details are required to calculate this tax rule"
            )
        if power_kw is None:
            raise InsufficientVehicleDataError(
                "Motor power (kW) is required to calculate tax for this vehicle"
            )
        if vehicle_age_years is None:
            raise InsufficientVehicleDataError(
                "Vehicle age is required to calculate tax for this vehicle"
            )

        power_value = Decimal(str(power_kw))
        age_value = Decimal(str(vehicle_age_years))
        vehicle_rule = (
            self.db.query(VehicleTaxRule)
            .filter(
                VehicleTaxRule.is_active.is_(True),
                VehicleTaxRule.fuel_type == fuel_type,
                VehicleTaxRule.category_code.in_(list(category_codes)),
                VehicleTaxRule.power_kw_min <= power_value,
                VehicleTaxRule.power_kw_max >= power_value,
                VehicleTaxRule.age_years_min <= age_value,
                VehicleTaxRule.age_years_max >= age_value,
            )
            .order_by(VehicleTaxRule.effective_date.desc(), VehicleTaxRule.created_at.desc())
            .first()
        )
        if vehicle_rule is None:
            raise NoTaxRuleError(
                f"No active tax rule found for {category_codes[0]} {fuel_type} {power_kw}kW"
            )

        customs_rule = (
            self.db.query(CustomsRule)
            .filter(CustomsRule.is_active.is_(True), CustomsRule.hs_code == vehicle_rule.hs_code)
            .order_by(CustomsRule.effective_date.desc(), CustomsRule.created_at.desc())
            .first()
        )
        surcharge_rule = (
            self.db.query(SurchargeRule)
            .filter(
                SurchargeRule.is_active.is_(True),
                SurchargeRule.applies_to == "CUSTOMS_DUTY",
            )
            .order_by(SurchargeRule.effective_date.desc(), SurchargeRule.created_at.desc())
            .first()
        )
        luxury_rule = (
            self.db.query(LuxuryTaxRule)
            .filter(
                LuxuryTaxRule.is_active.is_(True), LuxuryTaxRule.hs_code == vehicle_rule.hs_code
            )
            .order_by(LuxuryTaxRule.effective_date.desc(), LuxuryTaxRule.created_at.desc())
            .first()
        )
        return self._calculate_dedicated_duties(
            cif=Decimal(str(cif_value)),
            vehicle_rule=vehicle_rule,
            customs_rule=customs_rule,
            surcharge_rule=surcharge_rule,
            luxury_rule=luxury_rule,
            power_kw=power_kw,
        )

    def _validate_inputs(
        self,
        vehicle_type: str,
        fuel_type: str,
        engine_cc: int,
        cif_value: float,
        *,
        power_kw: float | None,
        vehicle_age_years: float | None,
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

        if power_kw is not None and power_kw < 0:
            raise ValueError(f"Invalid power_kw: {power_kw}. Must be non-negative")

        if vehicle_age_years is not None and vehicle_age_years < 0:
            raise ValueError(
                f"Invalid vehicle_age_years: {vehicle_age_years}. Must be non-negative"
            )

    def _find_matching_rule(
        self,
        vehicle_type: str,
        fuel_type: str,
        engine_cc: int,
        *,
        power_kw: float | None,
        vehicle_age_years: float | None,
        category_codes: list[str] | None,
    ) -> TaxRule | None:
        candidates = (
            self.db.query(TaxRule)
            .options(joinedload(TaxRule.gazette))
            .filter(
                TaxRule.vehicle_type == vehicle_type,
                TaxRule.fuel_type == fuel_type,
                TaxRule.is_active.is_(True),
            )
            .order_by(TaxRule.effective_date.desc())
        )
        allowed_categories = {code for code in (category_codes or []) if code}
        matching_rules: list[TaxRule] = []
        missing_messages: list[str] = []
        for rule in candidates:
            match, missing_message = self._rule_matches(
                rule,
                engine_cc=engine_cc,
                power_kw=power_kw,
                vehicle_age_years=vehicle_age_years,
                category_codes=allowed_categories,
            )
            if match:
                matching_rules.append(rule)
            elif missing_message:
                missing_messages.append(missing_message)

        if matching_rules:
            matching_rules.sort(
                key=lambda rule: (
                    self._specificity_score(rule),
                    rule.effective_date.toordinal(),
                    rule.created_at.timestamp(),
                ),
                reverse=True,
            )
            return matching_rules[0]

        if missing_messages:
            raise InsufficientVehicleDataError(missing_messages[0])
        return None

    def _rule_matches(
        self,
        rule: TaxRule,
        *,
        engine_cc: int,
        power_kw: float | None,
        vehicle_age_years: float | None,
        category_codes: set[str],
    ) -> tuple[bool, str | None]:
        if not (rule.engine_min <= engine_cc <= rule.engine_max):
            return False, None

        if rule.category_code:
            if not category_codes:
                return False, "Vehicle category details are required to calculate this tax rule"
            if rule.category_code not in category_codes:
                return False, None

        if rule.power_kw_min is not None or rule.power_kw_max is not None:
            if power_kw is None:
                return False, "Motor power (kW) is required to calculate tax for this vehicle"
            power_value = Decimal(str(power_kw))
            if rule.power_kw_min is not None and power_value < rule.power_kw_min:
                return False, None
            if rule.power_kw_max is not None and power_value > rule.power_kw_max:
                return False, None

        if rule.age_years_min is not None or rule.age_years_max is not None:
            if vehicle_age_years is None:
                return False, "Vehicle age is required to calculate tax for this vehicle"
            age_value = Decimal(str(vehicle_age_years))
            if rule.age_years_min is not None and age_value < rule.age_years_min:
                return False, None
            if rule.age_years_max is not None and age_value > rule.age_years_max:
                return False, None

        return True, None

    def _specificity_score(self, rule: TaxRule) -> int:
        score = 0
        if rule.category_code:
            score += 8
        if rule.power_kw_min is not None or rule.power_kw_max is not None:
            score += 4
        if rule.age_years_min is not None or rule.age_years_max is not None:
            score += 2
        if rule.engine_min != 0 or rule.engine_max != 999999:
            score += 1
        return score

    def _calculate_dedicated_duties(
        self,
        *,
        cif: Decimal,
        vehicle_rule: VehicleTaxRule,
        customs_rule: CustomsRule | None,
        surcharge_rule: SurchargeRule | None,
        luxury_rule: LuxuryTaxRule | None,
        power_kw: float,
    ) -> dict[str, Any]:
        customs_percent = (
            Decimal(str(customs_rule.customs_percent)) / Decimal("100")
            if customs_rule is not None
            else Decimal("0")
        )
        vat_percent = (
            Decimal(str(customs_rule.vat_percent)) / Decimal("100")
            if customs_rule is not None
            else Decimal("0")
        )
        pal_percent = (
            Decimal(str(customs_rule.pal_percent)) / Decimal("100")
            if customs_rule is not None
            else Decimal("0")
        )
        surcharge_percent = (
            Decimal(str(surcharge_rule.rate_percent)) / Decimal("100")
            if surcharge_rule is not None
            else Decimal("0")
        )

        customs = cif * customs_percent
        surcharge = customs * surcharge_percent
        if vehicle_rule.excise_type == "PER_KW":
            excise = Decimal(str(power_kw)) * Decimal(str(vehicle_rule.excise_rate))
        else:
            excise = cif * (Decimal(str(vehicle_rule.excise_rate)) / Decimal("100"))
        pal = cif * pal_percent

        cess = Decimal("0")
        cess_type = CessType.PERCENT.value
        cess_value = Decimal("0")
        if customs_rule is not None:
            cess_type = customs_rule.cess_type
            cess_value = Decimal(str(customs_rule.cess_value))
            if customs_rule.cess_type == CessType.FIXED.value:
                cess = cess_value
            else:
                cess = cif * (cess_value / Decimal("100"))

        vat_base = cif + customs + surcharge + excise + pal + cess
        vat = vat_base * vat_percent

        luxury_tax = Decimal("0")
        threshold_value: Decimal | None = None
        luxury_rate_percent: Decimal | None = None
        if luxury_rule is not None:
            threshold_value = Decimal(str(luxury_rule.threshold_value))
            luxury_rate_percent = Decimal(str(luxury_rule.rate_percent))
            if cif > threshold_value:
                luxury_tax = (cif - threshold_value) * (luxury_rate_percent / Decimal("100"))

        total_duty = customs + surcharge + excise + pal + cess + vat + luxury_tax
        total_landed_cost = cif + total_duty
        effective_rate = (total_duty / cif * Decimal("100")) if cif > 0 else Decimal("0")

        return {
            "cif_value": float(cif),
            "customs_duty": float(customs),
            "surcharge": float(surcharge),
            "excise_duty": float(excise),
            "cess": float(cess),
            "vat": float(vat),
            "pal": float(pal),
            "luxury_tax": float(luxury_tax),
            "total_duty": float(total_duty),
            "total_landed_cost": float(total_landed_cost),
            "effective_rate_percent": float(effective_rate),
            "rule_used": {
                "rule_source": "DEDICATED_RULE_TABLES",
                "category_code": vehicle_rule.category_code,
                "fuel_type": vehicle_rule.fuel_type,
                "hs_code": vehicle_rule.hs_code,
                "power_kw_min": float(vehicle_rule.power_kw_min),
                "power_kw_max": float(vehicle_rule.power_kw_max),
                "age_years_min": float(vehicle_rule.age_years_min),
                "age_years_max": float(vehicle_rule.age_years_max),
                "excise_type": vehicle_rule.excise_type,
                "excise_rate": float(vehicle_rule.excise_rate),
                "customs_percent": float(customs_rule.customs_percent) if customs_rule else 0.0,
                "vat_percent": float(customs_rule.vat_percent) if customs_rule else 0.0,
                "pal_percent": float(customs_rule.pal_percent) if customs_rule else 0.0,
                "cess_type": cess_type,
                "cess_value": float(cess_value),
                "surcharge_percent": float(surcharge_rule.rate_percent) if surcharge_rule else 0.0,
                "luxury_tax_threshold": (
                    float(threshold_value) if threshold_value is not None else None
                ),
                "luxury_tax_percent": (
                    float(luxury_rate_percent) if luxury_rate_percent is not None else None
                ),
            },
        }

    def _calculate_duties(
        self, cif: Decimal, rule: TaxRule, *, power_kw: float | None
    ) -> dict[str, Any]:
        customs_rate = Decimal(str(rule.customs_percent)) / Decimal("100")
        surcharge_rate = Decimal(str(rule.surcharge_percent)) / Decimal("100")
        excise_rate = Decimal(str(rule.excise_percent)) / Decimal("100")
        cess_rate = Decimal(str(rule.cess_percent)) / Decimal("100")
        vat_rate = Decimal(str(rule.vat_percent)) / Decimal("100")
        pal_rate = Decimal(str(rule.pal_percent)) / Decimal("100")
        luxury_rate = (
            Decimal(str(rule.luxury_tax_percent)) / Decimal("100")
            if rule.luxury_tax_percent is not None
            else Decimal("0")
        )

        customs = cif * customs_rate
        surcharge = customs * surcharge_rate

        apply_on = rule.apply_on
        if apply_on == ApplyOn.CUSTOMS_ONLY.value:
            base_for_excise = customs
        elif apply_on == ApplyOn.CIF.value:
            base_for_excise = cif
        else:
            base_for_excise = cif + customs + surcharge

        excise = base_for_excise * excise_rate
        if rule.excise_per_kw_amount is not None:
            if power_kw is None:
                raise InsufficientVehicleDataError(
                    "Motor power (kW) is required to calculate tax for this vehicle"
                )
            excise += Decimal(str(power_kw)) * Decimal(str(rule.excise_per_kw_amount))
        cess = base_for_excise * cess_rate

        if apply_on == ApplyOn.CIF_PLUS_EXCISE.value:
            taxable_value = cif + customs + surcharge + excise + cess
        else:
            taxable_value = cif + customs + surcharge + excise + cess

        vat = taxable_value * vat_rate
        pal = taxable_value * pal_rate
        luxury_tax = Decimal("0")
        if (
            rule.luxury_tax_threshold is not None
            and rule.luxury_tax_percent is not None
            and cif > rule.luxury_tax_threshold
        ):
            luxury_tax = cif * luxury_rate

        total_duty = customs + surcharge + excise + cess + vat + pal + luxury_tax
        total_landed_cost = cif + total_duty
        effective_rate = (total_duty / cif * Decimal("100")) if cif > 0 else Decimal("0")

        return {
            "cif_value": float(cif),
            "customs_duty": float(customs),
            "surcharge": float(surcharge),
            "excise_duty": float(excise),
            "cess": float(cess),
            "vat": float(vat),
            "pal": float(pal),
            "luxury_tax": float(luxury_tax),
            "total_duty": float(total_duty),
            "total_landed_cost": float(total_landed_cost),
            "effective_rate_percent": float(effective_rate),
        }


def calculate_tax(
    db: Session,
    vehicle_type: str,
    fuel_type: str,
    engine_cc: int,
    cif_value: float,
    *,
    power_kw: float | None = None,
    vehicle_age_years: float | None = None,
    category_codes: list[str] | None = None,
) -> dict[str, Any]:
    """Convenience wrapper for tax calculation."""
    calculator = TaxCalculator(db)
    result = calculator.calculate_import_duty(
        vehicle_type,
        fuel_type,
        engine_cc,
        cif_value,
        power_kw=power_kw,
        vehicle_age_years=vehicle_age_years,
        category_codes=category_codes,
    )
    logger.info(
        "Tax calculated: %s %s %scc CIF=%s total_duty=%s",
        vehicle_type,
        fuel_type,
        engine_cc,
        cif_value,
        result["total_duty"],
    )
    return result
