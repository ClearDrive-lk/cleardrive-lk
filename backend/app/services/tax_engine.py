"""
Versioned tax-rule catalog lookup service.
"""

from __future__ import annotations

from decimal import Decimal

from app.models.tax_rule_catalog import GlobalTaxParameter, HSCodeMatrixRule
from sqlalchemy.orm import Session


class TaxEngineLookupError(Exception):
    """Raised when a rule lookup resolves to zero or many active rows."""


class TaxEngine:
    """DB-backed lookup service for versioned global and HS-code tax rules."""

    def __init__(self, db: Session):
        self.db = db

    def get_global_param(
        self,
        *,
        parameter_group: str,
        parameter_name: str,
        condition_or_type: str,
    ) -> GlobalTaxParameter:
        matches = (
            self.db.query(GlobalTaxParameter)
            .filter(
                GlobalTaxParameter.is_active.is_(True),
                GlobalTaxParameter.parameter_group == parameter_group,
                GlobalTaxParameter.parameter_name == parameter_name,
                GlobalTaxParameter.condition_or_type == condition_or_type,
            )
            .order_by(GlobalTaxParameter.effective_date.desc(), GlobalTaxParameter.version.desc())
            .all()
        )
        if len(matches) != 1:
            raise TaxEngineLookupError(
                "Expected exactly one active global tax parameter for "
                f"{parameter_group}/{parameter_name}/{condition_or_type}, found {len(matches)}"
            )
        return matches[0]

    def resolve_hs_rule(
        self,
        *,
        vehicle_type: str,
        fuel_type: str,
        age_condition: str,
        capacity_input: float | Decimal,
        capacity_unit: str | None = None,
    ) -> HSCodeMatrixRule:
        capacity_value = Decimal(str(capacity_input))
        matches = (
            self.db.query(HSCodeMatrixRule)
            .filter(
                HSCodeMatrixRule.is_active.is_(True),
                HSCodeMatrixRule.vehicle_type == vehicle_type,
                HSCodeMatrixRule.fuel_type == fuel_type,
                HSCodeMatrixRule.age_condition == age_condition,
                HSCodeMatrixRule.capacity_unit == capacity_unit
                if capacity_unit is not None
                else True,
                HSCodeMatrixRule.capacity_min <= capacity_value,
                HSCodeMatrixRule.capacity_max >= capacity_value,
            )
            .order_by(HSCodeMatrixRule.effective_date.desc(), HSCodeMatrixRule.version.desc())
            .all()
        )
        if len(matches) != 1:
            raise TaxEngineLookupError(
                "Expected exactly one active HS-code rule for "
                f"{vehicle_type}/{fuel_type}/{age_condition}/{capacity_value}, found {len(matches)}"
            )
        return matches[0]


def get_global_param(db: Session, **kwargs: str) -> GlobalTaxParameter:
    return TaxEngine(db).get_global_param(**kwargs)


def resolve_hs_rule(
    db: Session,
    *,
    vehicle_type: str,
    fuel_type: str,
    age_condition: str,
    capacity_input: float | Decimal,
    capacity_unit: str | None = None,
) -> HSCodeMatrixRule:
    return TaxEngine(db).resolve_hs_rule(
        vehicle_type=vehicle_type,
        fuel_type=fuel_type,
        age_condition=age_condition,
        capacity_input=capacity_input,
        capacity_unit=capacity_unit,
    )
