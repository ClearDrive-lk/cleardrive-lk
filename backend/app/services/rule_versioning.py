"""
Helpers for versioned tax rule inserts with automatic superseding and audit logging.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.models.audit_log import AuditActionType, AuditEventType, AuditLog
from app.models.tax_rule_catalog import (
    GlobalTaxParameter,
    HSCodeMatrixRule,
    is_allowed_age_condition,
)
from sqlalchemy.orm import Session

_GLOBAL_FIELDS = (
    "parameter_group",
    "parameter_name",
    "condition_or_type",
    "value",
    "unit",
    "calculation_order",
    "applicability_flag",
    "effective_date",
    "version",
    "is_active",
)

_HS_FIELDS = (
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
    "min_excise_flat_rate_lkr",
    "effective_date",
    "version",
    "is_active",
)


def _serialize_model(instance: Any, fields: tuple[str, ...]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for field in fields:
        value = getattr(instance, field)
        if isinstance(value, Decimal):
            payload[field] = float(value)
        elif hasattr(value, "isoformat"):
            payload[field] = value.isoformat()
        else:
            payload[field] = value
    return payload


def _log_rule_audit(
    db: Session,
    *,
    admin_id: UUID | None,
    action_type: AuditActionType,
    table_name: str,
    record_id: str,
    old_value: dict[str, Any] | None,
    new_value: dict[str, Any] | None,
    change_reason: str,
    version: int,
) -> None:
    db.add(
        AuditLog(
            event_type=AuditEventType.TAX_RULES_ACTIVATED,
            admin_id=admin_id,
            action_type=action_type,
            table_name=table_name,
            record_id=record_id,
            old_value=old_value,
            new_value=new_value,
            change_reason=change_reason,
            version=version,
            details={
                "table_name": table_name,
                "record_id": record_id,
                "action_type": action_type.value,
                "version": version,
            },
        )
    )


class RuleVersioningService:
    """Non-disruptive versioning layer for CSV/admin-managed tax catalogs."""

    def __init__(self, db: Session):
        self.db = db

    def upsert_global_tax_parameter(
        self,
        *,
        parameter_group: str,
        parameter_name: str,
        condition_or_type: str,
        value: float | Decimal,
        unit: str,
        calculation_order: int,
        applicability_flag: str | None,
        effective_date,
        changed_by: UUID | None,
        change_reason: str,
    ) -> GlobalTaxParameter:
        existing = (
            self.db.query(GlobalTaxParameter)
            .filter(
                GlobalTaxParameter.is_active.is_(True),
                GlobalTaxParameter.parameter_group == parameter_group,
                GlobalTaxParameter.parameter_name == parameter_name,
                GlobalTaxParameter.condition_or_type == condition_or_type,
            )
            .order_by(GlobalTaxParameter.version.desc())
            .first()
        )
        previous_version = existing.version if existing else 0
        previous_payload = None
        if existing is not None:
            previous_payload = _serialize_model(
                existing,
                _GLOBAL_FIELDS,
            )
            existing.is_active = False
            existing.superseded_at = datetime.utcnow()

        record = GlobalTaxParameter(
            parameter_group=parameter_group,
            parameter_name=parameter_name,
            condition_or_type=condition_or_type,
            value=Decimal(str(value)),
            unit=unit,
            calculation_order=calculation_order,
            applicability_flag=applicability_flag,
            effective_date=effective_date,
            is_active=True,
            version=previous_version + 1,
        )
        self.db.add(record)
        self.db.flush()

        _log_rule_audit(
            self.db,
            admin_id=changed_by,
            action_type=AuditActionType.SUPERSEDE if existing else AuditActionType.CREATE,
            table_name=GlobalTaxParameter.__tablename__,
            record_id=str(record.id),
            old_value=previous_payload,
            new_value=_serialize_model(record, _GLOBAL_FIELDS),
            change_reason=change_reason,
            version=record.version,
        )
        return record

    def upsert_hs_code_matrix_rule(
        self,
        *,
        vehicle_type: str,
        fuel_type: str,
        age_condition: str,
        hs_code: str,
        capacity_min: float | Decimal,
        capacity_max: float | Decimal,
        capacity_unit: str,
        cid_pct: float | Decimal,
        pal_pct: float | Decimal,
        cess_pct: float | Decimal,
        excise_unit_rate_lkr: float | Decimal,
        min_excise_flat_rate_lkr: float | Decimal,
        effective_date,
        changed_by: UUID | None,
        change_reason: str,
    ) -> HSCodeMatrixRule:
        if not is_allowed_age_condition(age_condition):
            raise ValueError(f"Invalid age_condition: {age_condition}")

        min_value = Decimal(str(capacity_min))
        max_value = Decimal(str(capacity_max))
        if min_value > max_value:
            raise ValueError("capacity_min must be <= capacity_max")

        overlaps = (
            self.db.query(HSCodeMatrixRule)
            .filter(
                HSCodeMatrixRule.is_active.is_(True),
                HSCodeMatrixRule.vehicle_type == vehicle_type,
                HSCodeMatrixRule.fuel_type == fuel_type,
                HSCodeMatrixRule.age_condition == age_condition,
                HSCodeMatrixRule.capacity_min <= max_value,
                HSCodeMatrixRule.capacity_max >= min_value,
            )
            .order_by(HSCodeMatrixRule.version.desc())
            .all()
        )

        exact_match = next(
            (
                rule
                for rule in overlaps
                if rule.capacity_min == min_value and rule.capacity_max == max_value
            ),
            None,
        )
        if exact_match is None and overlaps:
            raise ValueError(
                "Overlapping active hs_code_matrix rule exists for "
                f"{vehicle_type}/{fuel_type}/{age_condition} {min_value}-{max_value}"
            )

        previous_version = exact_match.version if exact_match else 0
        previous_payload = None
        if exact_match is not None:
            previous_payload = _serialize_model(
                exact_match,
                _HS_FIELDS,
            )
            exact_match.is_active = False
            exact_match.superseded_at = datetime.utcnow()

        record = HSCodeMatrixRule(
            vehicle_type=vehicle_type,
            fuel_type=fuel_type,
            age_condition=age_condition,
            hs_code=hs_code,
            capacity_min=min_value,
            capacity_max=max_value,
            capacity_unit=capacity_unit,
            cid_pct=Decimal(str(cid_pct)),
            pal_pct=Decimal(str(pal_pct)),
            cess_pct=Decimal(str(cess_pct)),
            excise_unit_rate_lkr=Decimal(str(excise_unit_rate_lkr)),
            min_excise_flat_rate_lkr=Decimal(str(min_excise_flat_rate_lkr)),
            effective_date=effective_date,
            is_active=True,
            version=previous_version + 1,
        )
        self.db.add(record)
        self.db.flush()

        _log_rule_audit(
            self.db,
            admin_id=changed_by,
            action_type=AuditActionType.SUPERSEDE if exact_match else AuditActionType.CREATE,
            table_name=HSCodeMatrixRule.__tablename__,
            record_id=str(record.id),
            old_value=previous_payload,
            new_value=_serialize_model(record, _HS_FIELDS),
            change_reason=change_reason,
            version=record.version,
        )
        return record

    def supersede_overlapping_hs_code_matrix_rules(
        self,
        *,
        rows: list[dict[str, Any]],
        changed_by: UUID | None,
        change_reason: str,
    ) -> int:
        superseded = 0
        seen_ids: set[UUID] = set()

        for row in rows:
            min_value = Decimal(str(row["capacity_min"]))
            max_value = Decimal(str(row["capacity_max"]))
            overlaps = (
                self.db.query(HSCodeMatrixRule)
                .filter(
                    HSCodeMatrixRule.is_active.is_(True),
                    HSCodeMatrixRule.vehicle_type == str(row["vehicle_type"]),
                    HSCodeMatrixRule.fuel_type == str(row["fuel_type"]),
                    HSCodeMatrixRule.age_condition == str(row["age_condition"]),
                    HSCodeMatrixRule.capacity_min <= max_value,
                    HSCodeMatrixRule.capacity_max >= min_value,
                )
                .all()
            )

            for rule in overlaps:
                if rule.id in seen_ids:
                    continue
                if rule.capacity_min == min_value and rule.capacity_max == max_value:
                    continue
                self.deactivate_hs_code_matrix_rule(
                    record=rule,
                    changed_by=changed_by,
                    change_reason=change_reason,
                )
                seen_ids.add(rule.id)
                superseded += 1

        return superseded

    def update_global_tax_parameter(
        self,
        *,
        record: GlobalTaxParameter,
        parameter_group: str,
        parameter_name: str,
        condition_or_type: str,
        value: float | Decimal,
        unit: str,
        calculation_order: int,
        applicability_flag: str | None,
        effective_date,
        changed_by: UUID | None,
        change_reason: str,
    ) -> GlobalTaxParameter:
        previous_payload = _serialize_model(record, _GLOBAL_FIELDS)
        record.is_active = False
        record.superseded_at = datetime.utcnow()

        new_record = self.upsert_global_tax_parameter(
            parameter_group=parameter_group,
            parameter_name=parameter_name,
            condition_or_type=condition_or_type,
            value=value,
            unit=unit,
            calculation_order=calculation_order,
            applicability_flag=applicability_flag,
            effective_date=effective_date,
            changed_by=changed_by,
            change_reason=change_reason,
        )
        _log_rule_audit(
            self.db,
            admin_id=changed_by,
            action_type=AuditActionType.UPDATE,
            table_name=GlobalTaxParameter.__tablename__,
            record_id=str(new_record.id),
            old_value=previous_payload,
            new_value=_serialize_model(new_record, _GLOBAL_FIELDS),
            change_reason=change_reason,
            version=new_record.version,
        )
        return new_record

    def update_hs_code_matrix_rule(
        self,
        *,
        record: HSCodeMatrixRule,
        vehicle_type: str,
        fuel_type: str,
        age_condition: str,
        hs_code: str,
        capacity_min: float | Decimal,
        capacity_max: float | Decimal,
        capacity_unit: str,
        cid_pct: float | Decimal,
        pal_pct: float | Decimal,
        cess_pct: float | Decimal,
        excise_unit_rate_lkr: float | Decimal,
        min_excise_flat_rate_lkr: float | Decimal,
        effective_date,
        changed_by: UUID | None,
        change_reason: str,
    ) -> HSCodeMatrixRule:
        previous_payload = _serialize_model(record, _HS_FIELDS)
        record.is_active = False
        record.superseded_at = datetime.utcnow()

        new_record = self.upsert_hs_code_matrix_rule(
            vehicle_type=vehicle_type,
            fuel_type=fuel_type,
            age_condition=age_condition,
            hs_code=hs_code,
            capacity_min=capacity_min,
            capacity_max=capacity_max,
            capacity_unit=capacity_unit,
            cid_pct=cid_pct,
            pal_pct=pal_pct,
            cess_pct=cess_pct,
            excise_unit_rate_lkr=excise_unit_rate_lkr,
            min_excise_flat_rate_lkr=min_excise_flat_rate_lkr,
            effective_date=effective_date,
            changed_by=changed_by,
            change_reason=change_reason,
        )
        _log_rule_audit(
            self.db,
            admin_id=changed_by,
            action_type=AuditActionType.UPDATE,
            table_name=HSCodeMatrixRule.__tablename__,
            record_id=str(new_record.id),
            old_value=previous_payload,
            new_value=_serialize_model(new_record, _HS_FIELDS),
            change_reason=change_reason,
            version=new_record.version,
        )
        return new_record

    def deactivate_global_tax_parameter(
        self, *, record: GlobalTaxParameter, changed_by: UUID | None, change_reason: str
    ) -> None:
        previous_payload = _serialize_model(record, _GLOBAL_FIELDS)
        record.is_active = False
        record.superseded_at = datetime.utcnow()
        _log_rule_audit(
            self.db,
            admin_id=changed_by,
            action_type=AuditActionType.DELETE,
            table_name=GlobalTaxParameter.__tablename__,
            record_id=str(record.id),
            old_value=previous_payload,
            new_value=None,
            change_reason=change_reason,
            version=record.version,
        )

    def deactivate_hs_code_matrix_rule(
        self, *, record: HSCodeMatrixRule, changed_by: UUID | None, change_reason: str
    ) -> None:
        previous_payload = _serialize_model(record, _HS_FIELDS)
        record.is_active = False
        record.superseded_at = datetime.utcnow()
        _log_rule_audit(
            self.db,
            admin_id=changed_by,
            action_type=AuditActionType.DELETE,
            table_name=HSCodeMatrixRule.__tablename__,
            record_id=str(record.id),
            old_value=previous_payload,
            new_value=None,
            change_reason=change_reason,
            version=record.version,
        )
