from __future__ import annotations

from datetime import date

import pytest
from app.models.audit_log import AuditActionType, AuditLog
from app.models.tax_rule_catalog import GlobalTaxParameter
from app.services.rule_versioning import RuleVersioningService
from app.services.tax_engine import TaxEngine, TaxEngineLookupError


def test_upsert_global_tax_parameter_supersedes_and_audits(db, admin_user):
    service = RuleVersioningService(db)

    first = service.upsert_global_tax_parameter(
        parameter_group="VAT",
        parameter_name="standard_rate",
        condition_or_type="DEFAULT",
        value=18,
        unit="PERCENT",
        calculation_order=7,
        applicability_flag="ALL",
        effective_date=date(2026, 3, 20),
        changed_by=admin_user.id,
        change_reason="initial seed",
    )
    db.commit()

    second = service.upsert_global_tax_parameter(
        parameter_group="VAT",
        parameter_name="standard_rate",
        condition_or_type="DEFAULT",
        value=20,
        unit="PERCENT",
        calculation_order=7,
        applicability_flag="ALL",
        effective_date=date(2026, 4, 1),
        changed_by=admin_user.id,
        change_reason="budget update",
    )
    db.commit()

    db.refresh(first)
    db.refresh(second)

    assert first.is_active is False
    assert first.superseded_at is not None
    assert second.is_active is True
    assert second.version == 2

    audit_logs = db.query(AuditLog).filter(AuditLog.table_name == "global_tax_parameters").all()
    assert len(audit_logs) == 2
    assert audit_logs[-1].action_type == AuditActionType.SUPERSEDE
    assert audit_logs[-1].old_value["value"] == 18.0
    assert audit_logs[-1].new_value["value"] == 20.0
    assert audit_logs[-1].change_reason == "budget update"


def test_upsert_hs_code_matrix_rule_supersedes_exact_match_and_resolves(db, admin_user):
    service = RuleVersioningService(db)

    original = service.upsert_hs_code_matrix_rule(
        vehicle_type="PASSENGER",
        fuel_type="ELECTRIC",
        age_condition="<=1",
        hs_code="8703.80.31",
        capacity_min=0,
        capacity_max=50,
        capacity_unit="KW",
        cid_pct=0,
        pal_pct=0,
        cess_pct=0,
        excise_unit_rate_lkr=18000,
        min_excise_flat_rate_lkr=990000,
        effective_date=date(2026, 3, 20),
        changed_by=admin_user.id,
        change_reason="initial import",
    )
    db.commit()

    updated = service.upsert_hs_code_matrix_rule(
        vehicle_type="PASSENGER",
        fuel_type="ELECTRIC",
        age_condition="<=1",
        hs_code="8703.80.31",
        capacity_min=0,
        capacity_max=50,
        capacity_unit="KW",
        cid_pct=0,
        pal_pct=0,
        cess_pct=0,
        excise_unit_rate_lkr=18100,
        min_excise_flat_rate_lkr=1992000,
        effective_date=date(2026, 4, 1),
        changed_by=admin_user.id,
        change_reason="gazette supersede",
    )
    db.commit()

    db.refresh(original)
    db.refresh(updated)

    assert original.is_active is False
    assert updated.is_active is True
    assert updated.version == 2

    resolved = TaxEngine(db).resolve_hs_rule(
        vehicle_type="PASSENGER",
        fuel_type="ELECTRIC",
        age_condition="<=1",
        capacity_input=40,
    )
    assert resolved.id == updated.id
    assert float(resolved.excise_unit_rate_lkr) == 18100.0
    assert float(resolved.min_excise_flat_rate_lkr) == 1992000.0


def test_upsert_hs_code_matrix_rule_rejects_overlap(db, admin_user):
    service = RuleVersioningService(db)

    service.upsert_hs_code_matrix_rule(
        vehicle_type="PASSENGER",
        fuel_type="ELECTRIC",
        age_condition="<=1",
        hs_code="8703.80.31",
        capacity_min=0,
        capacity_max=50,
        capacity_unit="KW",
        cid_pct=0,
        pal_pct=0,
        cess_pct=0,
        excise_unit_rate_lkr=18100,
        min_excise_flat_rate_lkr=0,
        effective_date=date(2026, 3, 20),
        changed_by=admin_user.id,
        change_reason="initial import",
    )
    db.commit()

    with pytest.raises(ValueError, match="Overlapping active hs_code_matrix rule exists"):
        service.upsert_hs_code_matrix_rule(
            vehicle_type="PASSENGER",
            fuel_type="ELECTRIC",
            age_condition="<=1",
            hs_code="8703.80.32",
            capacity_min=40,
            capacity_max=100,
            capacity_unit="KW",
            cid_pct=0,
            pal_pct=0,
            cess_pct=0,
            excise_unit_rate_lkr=24100,
            min_excise_flat_rate_lkr=0,
            effective_date=date(2026, 4, 1),
            changed_by=admin_user.id,
            change_reason="invalid overlap",
        )


def test_supersede_overlapping_hs_code_matrix_rules_allows_range_split(db, admin_user):
    service = RuleVersioningService(db)

    original = service.upsert_hs_code_matrix_rule(
        vehicle_type="HYBRID",
        fuel_type="PETROL",
        age_condition="<=1",
        hs_code="8703.40.35",
        capacity_min=0,
        capacity_max=1500,
        capacity_unit="CC",
        cid_pct=20,
        pal_pct=0,
        cess_pct=0,
        excise_unit_rate_lkr=3450,
        min_excise_flat_rate_lkr=0,
        effective_date=date(2025, 5, 1),
        changed_by=admin_user.id,
        change_reason="initial import",
    )
    db.commit()

    superseded = service.supersede_overlapping_hs_code_matrix_rules(
        rows=[
            {
                "vehicle_type": "HYBRID",
                "fuel_type": "PETROL",
                "age_condition": "<=1",
                "hs_code": "8703.40.35",
                "capacity_min": 0,
                "capacity_max": 1000,
                "capacity_unit": "CC",
                "cid_pct": 20,
                "pal_pct": 0,
                "cess_pct": 0,
                "excise_unit_rate_lkr": 3450,
                "min_excise_flat_rate_lkr": 0,
            },
            {
                "vehicle_type": "HYBRID",
                "fuel_type": "PETROL",
                "age_condition": "<=1",
                "hs_code": "8703.40.58",
                "capacity_min": 1001,
                "capacity_max": 1500,
                "capacity_unit": "CC",
                "cid_pct": 20,
                "pal_pct": 0,
                "cess_pct": 0,
                "excise_unit_rate_lkr": 4450,
                "min_excise_flat_rate_lkr": 0,
            },
        ],
        changed_by=admin_user.id,
        change_reason="split range",
    )
    db.commit()
    db.refresh(original)

    assert superseded == 1
    assert original.is_active is False


def test_tax_engine_get_global_param_requires_exact_single_active_row(db, admin_user):
    service = RuleVersioningService(db)
    service.upsert_global_tax_parameter(
        parameter_group="SSCL",
        parameter_name="rate",
        condition_or_type="DEFAULT",
        value=2.5,
        unit="PERCENT",
        calculation_order=6,
        applicability_flag="ALL",
        effective_date=date(2026, 3, 20),
        changed_by=admin_user.id,
        change_reason="initial seed",
    )
    db.commit()

    match = TaxEngine(db).get_global_param(
        parameter_group="SSCL",
        parameter_name="rate",
        condition_or_type="DEFAULT",
    )
    assert float(match.value) == 2.5

    db.add(
        GlobalTaxParameter(
            parameter_group="SSCL",
            parameter_name="rate",
            condition_or_type="DEFAULT",
            value=3.0,
            unit="PERCENT",
            calculation_order=6,
            applicability_flag="ALL",
            effective_date=date(2026, 3, 21),
            is_active=True,
            version=99,
        )
    )
    db.commit()

    with pytest.raises(
        TaxEngineLookupError, match="Expected exactly one active global tax parameter"
    ):
        TaxEngine(db).get_global_param(
            parameter_group="SSCL",
            parameter_name="rate",
            condition_or_type="DEFAULT",
        )
