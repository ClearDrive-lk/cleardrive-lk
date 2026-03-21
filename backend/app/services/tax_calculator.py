"""
Tax calculator service for vehicle import duties.

Pure Python deterministic calculation logic backed by DB tax rules.
Story: CD-22
"""

from __future__ import annotations

import logging
from datetime import date
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
from app.models.tax_rule_catalog import GlobalTaxParameter, HSCodeMatrixRule
from app.services.tax_engine import TaxEngine, TaxEngineLookupError
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
        catalog_vehicle_type: str | None = None,
        catalog_fuel_type: str | None = None,
        vehicle_condition: str | None = None,
        import_date: date | None = None,
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
            return self._augment_result_with_fixed_fees(dedicated_result)

        catalog_result = self._calculate_with_catalog_rules(
            cif_value=cif_value,
            vehicle_type=vehicle_type,
            fuel_type=fuel_type,
            engine_cc=engine_cc,
            power_kw=power_kw,
            vehicle_age_years=vehicle_age_years,
            category_codes=category_codes,
            catalog_vehicle_type=catalog_vehicle_type,
            catalog_fuel_type=catalog_fuel_type,
            vehicle_condition=vehicle_condition,
            import_date=import_date,
        )
        if catalog_result is not None:
            return self._augment_result_with_fixed_fees(catalog_result)

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
        return self._augment_result_with_fixed_fees(result)

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

    def _calculate_with_catalog_rules(
        self,
        *,
        cif_value: float,
        vehicle_type: str,
        fuel_type: str,
        engine_cc: int,
        power_kw: float | None,
        vehicle_age_years: float | None,
        category_codes: list[str] | None,
        catalog_vehicle_type: str | None,
        catalog_fuel_type: str | None,
        vehicle_condition: str | None,
        import_date: date | None,
    ) -> dict[str, Any] | None:
        active_catalog_rule_count = (
            self.db.query(HSCodeMatrixRule).filter(HSCodeMatrixRule.is_active.is_(True)).count()
        )
        if active_catalog_rule_count == 0:
            return None

        if vehicle_age_years is None:
            raise InsufficientVehicleDataError(
                "Vehicle age is required to calculate tax for this vehicle"
            )

        resolved_catalog_vehicle_type, resolved_catalog_fuel_type = self._resolve_catalog_identity(
            vehicle_type=vehicle_type,
            fuel_type=fuel_type,
            category_codes=category_codes,
            catalog_vehicle_type=catalog_vehicle_type,
            catalog_fuel_type=catalog_fuel_type,
        )
        if resolved_catalog_vehicle_type is None or resolved_catalog_fuel_type is None:
            return None

        capacity_input = self._resolve_catalog_capacity_input(
            catalog_vehicle_type=resolved_catalog_vehicle_type,
            engine_cc=engine_cc,
            power_kw=power_kw,
        )

        hs_rule = self._resolve_catalog_hs_rule(
            vehicle_type=resolved_catalog_vehicle_type,
            fuel_type=resolved_catalog_fuel_type,
            vehicle_age_years=vehicle_age_years,
            capacity_input=capacity_input,
        )
        if hs_rule is None:
            return None

        vat_rate = self._require_global_rate(
            parameter_group="GENERAL_TAX",
            parameter_name="VAT",
            condition_or_type="STANDARD_RATE",
        )
        surcharge_rate = self._resolve_surcharge_rate(
            vehicle_age_years=vehicle_age_years,
            vehicle_condition=vehicle_condition,
            import_date=import_date,
        )
        luxury_config = self._resolve_luxury_tax_config(
            catalog_vehicle_type=resolved_catalog_vehicle_type,
            catalog_fuel_type=resolved_catalog_fuel_type,
        )
        statutory_uplift_rate = self._resolve_statutory_uplift_rate()

        return self._calculate_catalog_duties(
            cif=Decimal(str(cif_value)),
            hs_rule=hs_rule,
            capacity_input=capacity_input,
            surcharge_rate=surcharge_rate,
            vat_rate=vat_rate,
            luxury_config=luxury_config,
            statutory_uplift_rate=statutory_uplift_rate,
        )

    def _resolve_catalog_identity(
        self,
        *,
        vehicle_type: str,
        fuel_type: str,
        category_codes: list[str] | None,
        catalog_vehicle_type: str | None,
        catalog_fuel_type: str | None,
    ) -> tuple[str | None, str | None]:
        if catalog_vehicle_type and catalog_fuel_type:
            normalized = self._normalize_catalog_identity(
                catalog_vehicle_type=catalog_vehicle_type,
                catalog_fuel_type=catalog_fuel_type,
            )
            if normalized != (None, None):
                return normalized

        if fuel_type == TaxFuelType.ELECTRIC.value:
            return "ELECTRIC", "ELECTRIC"
        if fuel_type == TaxFuelType.HYBRID.value:
            return "HYBRID", "PETROL"
        if vehicle_type == TaxVehicleType.TRUCK.value:
            if fuel_type == TaxFuelType.DIESEL.value:
                return "COMMERCIAL_TRUCK", "DIESEL"
            if fuel_type == TaxFuelType.PETROL.value:
                return "COMMERCIAL_TRUCK", "PETROL"
        if fuel_type == TaxFuelType.DIESEL.value:
            return "PASSENGER_CAR", "DIESEL"
        if fuel_type == TaxFuelType.PETROL.value:
            return "PASSENGER_CAR", "PETROL"
        if category_codes and any(code == "GOODS_VEHICLE_ELECTRIC" for code in category_codes):
            return "COMMERCIAL_TRUCK", "ELECTRIC"
        return None, None

    def _normalize_catalog_identity(
        self,
        *,
        catalog_vehicle_type: str,
        catalog_fuel_type: str,
    ) -> tuple[str | None, str | None]:
        vehicle_value = str(catalog_vehicle_type or "").strip().lower()
        fuel_value = str(catalog_fuel_type or "").strip().lower()

        if "electric" in fuel_value or "electric" in vehicle_value:
            return "ELECTRIC", "ELECTRIC"
        if "hybrid" in fuel_value or "hybrid" in vehicle_value:
            if "diesel" in fuel_value:
                return "HYBRID", "DIESEL"
            return "HYBRID", "PETROL"
        if "truck" in vehicle_value or "pickup" in vehicle_value or "commercial" in vehicle_value:
            if "diesel" in fuel_value:
                return "COMMERCIAL_TRUCK", "DIESEL"
            if "petrol" in fuel_value or "gasoline" in fuel_value:
                return "COMMERCIAL_TRUCK", "PETROL"
        if "diesel" in fuel_value:
            return "PASSENGER_CAR", "DIESEL"
        if "petrol" in fuel_value or "gasoline" in fuel_value:
            return "PASSENGER_CAR", "PETROL"
        return None, None

    def _resolve_catalog_capacity_input(
        self,
        *,
        catalog_vehicle_type: str,
        engine_cc: int,
        power_kw: float | None,
    ) -> Decimal:
        if catalog_vehicle_type == "ELECTRIC":
            if power_kw is None:
                raise InsufficientVehicleDataError(
                    "Motor power (kW) is required to calculate tax for this vehicle"
                )
            return Decimal(str(power_kw))
        return Decimal(str(engine_cc))

    def _resolve_catalog_hs_rule(
        self,
        *,
        vehicle_type: str,
        fuel_type: str,
        vehicle_age_years: float,
        capacity_input: Decimal,
    ) -> HSCodeMatrixRule | None:
        age_condition_candidates = self._catalog_age_condition_candidates(vehicle_age_years)
        engine = TaxEngine(self.db)
        for age_condition in age_condition_candidates:
            try:
                return engine.resolve_hs_rule(
                    vehicle_type=vehicle_type,
                    fuel_type=fuel_type,
                    age_condition=age_condition,
                    capacity_input=capacity_input,
                )
            except TaxEngineLookupError:
                continue
        return None

    def _catalog_age_condition_candidates(self, vehicle_age_years: float) -> list[str]:
        if vehicle_age_years <= 1:
            return ["<=1"]
        if vehicle_age_years <= 2:
            return [">1-2", ">1-3"]
        if vehicle_age_years <= 3:
            return [">2-3", ">1-3"]
        if vehicle_age_years <= 5:
            return [">3-5"]
        if vehicle_age_years <= 10:
            return [">5-10"]
        return [">10"]

    def _require_global_rate(
        self,
        *,
        parameter_group: str,
        parameter_name: str,
        condition_or_type: str,
    ) -> Decimal:
        try:
            record = TaxEngine(self.db).get_global_param(
                parameter_group=parameter_group,
                parameter_name=parameter_name,
                condition_or_type=condition_or_type,
            )
        except TaxEngineLookupError as exc:
            raise NoTaxRuleError(
                "Approved catalog tax parameters are incomplete for this vehicle"
            ) from exc
        return Decimal(str(record.value))

    def _find_optional_global_param(
        self,
        *,
        parameter_group: str,
        parameter_name: str,
        condition_or_types: list[str],
    ) -> GlobalTaxParameter | None:
        engine = TaxEngine(self.db)
        for condition_or_type in condition_or_types:
            try:
                return engine.get_global_param(
                    parameter_group=parameter_group,
                    parameter_name=parameter_name,
                    condition_or_type=condition_or_type,
                )
            except TaxEngineLookupError:
                continue
        return None

    def _resolve_vehicle_condition(
        self, *, vehicle_condition: str | None, vehicle_age_years: float | None
    ) -> str:
        if vehicle_condition is not None:
            normalized = vehicle_condition.strip().upper()
            if normalized in {"BRAND_NEW", "NEW"}:
                return "BRAND_NEW"
            if normalized in {"USED", "PREOWNED", "PRE_OWNED"}:
                return "USED"
        if vehicle_age_years is not None and vehicle_age_years <= 1:
            return "BRAND_NEW"
        return "USED"

    def _resolve_surcharge_rate(
        self,
        *,
        vehicle_age_years: float,
        vehicle_condition: str | None,
        import_date: date | None,
    ) -> Decimal:
        resolved_condition = self._resolve_vehicle_condition(
            vehicle_condition=vehicle_condition,
            vehicle_age_years=vehicle_age_years,
        )
        condition_candidates: list[str]
        reference_date = import_date or date.today()
        if resolved_condition == "BRAND_NEW":
            condition_candidates = ["BRAND_NEW"]
        elif reference_date < date(2026, 4, 1):
            condition_candidates = ["IMPORT_DATE<2026-04-01", "USED_AND_AFTER_2026-04-01"]
        else:
            condition_candidates = ["USED_AND_AFTER_2026-04-01", "IMPORT_DATE<2026-04-01"]
        record = self._find_optional_global_param(
            parameter_group="CUSTOMS_RULE",
            parameter_name="SURCHARGE_RATE",
            condition_or_types=condition_candidates,
        )
        return Decimal(str(record.value)) if record is not None else Decimal("0")

    def _resolve_fixed_fee(self, *, parameter_name: str) -> Decimal:
        record = self._find_optional_global_param(
            parameter_group="FIXED_FEES",
            parameter_name=parameter_name,
            condition_or_types=["PER_UNIT", "ALL", "DEFAULT"],
        )
        if record is None:
            record = self._find_optional_global_param(
                parameter_group="GENERAL_TAX",
                parameter_name=parameter_name,
                condition_or_types=["ALL", "DEFAULT", "STANDARD_RATE", "FIXED_FEE", "FLAT_RATE"],
            )
        return Decimal(str(record.value)) if record is not None else Decimal("0")

    def _resolve_statutory_uplift_rate(self) -> Decimal:
        record = self._find_optional_global_param(
            parameter_group="CUSTOMS_RULE",
            parameter_name="STATUTORY_UPLIFT_BASE",
            condition_or_types=["ALL", "DEFAULT"],
        )
        return Decimal(str(record.value)) if record is not None else Decimal("0")

    def _augment_result_with_fixed_fees(self, result: dict[str, Any]) -> dict[str, Any]:
        vel = self._resolve_fixed_fee(parameter_name="VEL")
        com_exm_sel = self._resolve_fixed_fee(parameter_name="COM_EXM_SEL")
        total_payable_to_customs = Decimal(str(result["total_duty"])) + vel + com_exm_sel
        total_landed_cost = Decimal(str(result["cif_value"])) + total_payable_to_customs
        effective_rate = (
            total_payable_to_customs / Decimal(str(result["cif_value"])) * Decimal("100")
            if Decimal(str(result["cif_value"])) > 0
            else Decimal("0")
        )

        result["vel"] = float(vel)
        result["com_exm_sel"] = float(com_exm_sel)
        result["total_payable_to_customs"] = float(total_payable_to_customs)
        result["total_landed_cost"] = float(total_landed_cost)
        result["effective_rate_percent"] = float(effective_rate)
        rule_used = result.get("rule_used")
        if isinstance(rule_used, dict):
            rule_used["vel"] = float(vel)
            rule_used["com_exm_sel"] = float(com_exm_sel)
        return result

    def _resolve_luxury_tax_config(
        self,
        *,
        catalog_vehicle_type: str,
        catalog_fuel_type: str,
    ) -> tuple[Decimal, Decimal] | None:
        vehicle_value = str(catalog_vehicle_type or "").strip().lower()
        fuel_value = str(catalog_fuel_type or "").strip().lower()

        if "truck" in vehicle_value or "pickup" in vehicle_value or "commercial" in vehicle_value:
            return None

        threshold_name: str
        rate_name: str
        condition_or_type: str
        if "electric" in fuel_value or "electric" in vehicle_value:
            threshold_name = "THRESHOLD_EV"
            rate_name = "RATE_EV"
            condition_or_type = "ELECTRIC"
        elif "hybrid" in fuel_value or "hybrid" in vehicle_value:
            if "diesel" in fuel_value:
                threshold_name = "THRESHOLD_HYBRID_DIESEL"
                rate_name = "RATE_HYBRID_DIESEL"
                condition_or_type = "HYBRID"
            else:
                threshold_name = "THRESHOLD_HYBRID_PETROL"
                rate_name = "RATE_HYBRID_PETROL"
                condition_or_type = "HYBRID"
        elif "diesel" in fuel_value:
            threshold_name = "THRESHOLD_DIESEL"
            rate_name = "RATE_DIESEL"
            condition_or_type = "PASSENGER_CAR"
        else:
            threshold_name = "THRESHOLD_PETROL"
            rate_name = "RATE_PETROL"
            condition_or_type = "PASSENGER_CAR"

        threshold_record = self._find_optional_global_param(
            parameter_group="LUXURY_TAX",
            parameter_name=threshold_name,
            condition_or_types=[condition_or_type],
        )
        rate_record = self._find_optional_global_param(
            parameter_group="LUXURY_TAX",
            parameter_name=rate_name,
            condition_or_types=["ON_EXCESS_VALUE"],
        )
        if threshold_record is None or rate_record is None:
            return None
        return Decimal(str(threshold_record.value)), Decimal(str(rate_record.value))

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

    def _calculate_catalog_duties(
        self,
        *,
        cif: Decimal,
        hs_rule: HSCodeMatrixRule,
        capacity_input: Decimal,
        surcharge_rate: Decimal,
        vat_rate: Decimal,
        luxury_config: tuple[Decimal, Decimal] | None,
        statutory_uplift_rate: Decimal,
    ) -> dict[str, Any]:
        customs_percent = Decimal(str(hs_rule.cid_pct)) / Decimal("100")
        pal_percent = Decimal(str(hs_rule.pal_pct)) / Decimal("100")
        cess_percent = Decimal(str(hs_rule.cess_pct)) / Decimal("100")
        surcharge_percent = surcharge_rate / Decimal("100")
        vat_percent = vat_rate / Decimal("100")
        uplift_multiplier = Decimal("1") + (statutory_uplift_rate / Decimal("100"))

        customs = cif * customs_percent
        surcharge = customs * surcharge_percent
        calculated_cc_excise = capacity_input * Decimal(str(hs_rule.excise_unit_rate_lkr))
        min_excise_flat_rate = Decimal(str(hs_rule.min_excise_flat_rate_lkr))
        excise = max(calculated_cc_excise, min_excise_flat_rate)
        pal = cif * pal_percent
        cess = cif * cess_percent
        vat_base = (cif * uplift_multiplier) + customs + surcharge + excise + pal + cess
        vat = vat_base * vat_percent

        luxury_tax = Decimal("0")
        threshold_value: Decimal | None = None
        luxury_rate_percent: Decimal | None = None
        if luxury_config is not None:
            threshold_value, luxury_rate_percent = luxury_config
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
                "rule_source": "CATALOG_RULE_TABLES",
                "vehicle_type": hs_rule.vehicle_type,
                "fuel_type": hs_rule.fuel_type,
                "age_condition": hs_rule.age_condition,
                "hs_code": hs_rule.hs_code,
                "capacity_min": float(hs_rule.capacity_min),
                "capacity_max": float(hs_rule.capacity_max),
                "capacity_unit": hs_rule.capacity_unit,
                "capacity_input": float(capacity_input),
                "customs_percent": float(hs_rule.cid_pct),
                "surcharge_percent": float(surcharge_rate),
                "excise_rate": float(hs_rule.excise_unit_rate_lkr),
                "min_excise_flat_rate_lkr": float(hs_rule.min_excise_flat_rate_lkr),
                "calculated_cc_excise": float(calculated_cc_excise),
                "statutory_uplift_rate": float(statutory_uplift_rate),
                "vat_base": float(vat_base),
                "vat_percent": float(vat_rate),
                "pal_percent": float(hs_rule.pal_pct),
                "cess_percent": float(hs_rule.cess_pct),
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
    catalog_vehicle_type: str | None = None,
    catalog_fuel_type: str | None = None,
    vehicle_condition: str | None = None,
    import_date: date | None = None,
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
        catalog_vehicle_type=catalog_vehicle_type,
        catalog_fuel_type=catalog_fuel_type,
        vehicle_condition=vehicle_condition,
        import_date=import_date,
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
