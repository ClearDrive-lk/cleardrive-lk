"""Tests for CD-24 gazette extraction upload pipeline."""

from __future__ import annotations

from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.models.audit_log import AuditEventType, AuditLog
from app.models.gazette import Gazette, TaxRule
from app.models.tax_rule_catalog import GlobalTaxParameter, HSCodeMatrixRule
from app.services.gazette_fallback_parser import (
    parse_ocr_to_rules,
    sanitize_electric_vehicle_rules,
)
from app.services.gemini import GeminiService


def test_upload_gazette_success(client, admin_headers, mocker):
    mocker.patch(
        "app.modules.gazette.routes.document_ai_service.parse_gazette_pdf",
        new=AsyncMock(
            return_value={
                "text": "Gazette text",
                "tables": [{"headers": ["Vehicle Type"], "rows": [{"Vehicle Type": "SEDAN"}]}],
                "pages": 2,
                "confidence": 0.94,
            }
        ),
    )
    mocker.patch(
        "app.modules.gazette.routes.gemini_service.structure_gazette",
        new=AsyncMock(
            return_value={
                "gazette_no": "2024/01",
                "effective_date": "2024-02-01",
                "rules": [
                    {
                        "vehicle_type": "SEDAN",
                        "fuel_type": "PETROL",
                        "engine_min": 1000,
                        "engine_max": 1500,
                        "customs_percent": 25.0,
                        "excise_percent": 50.0,
                        "vat_percent": 15.0,
                        "pal_percent": 7.5,
                        "cess_percent": 0.0,
                        "apply_on": "CIF_PLUS_CUSTOMS",
                        "notes": "standard",
                    }
                ],
            }
        ),
    )

    response = client.post(
        "/api/v1/gazette/upload",
        headers=admin_headers,
        files={"file": ("gazette.pdf", BytesIO(b"%PDF-1.4 test"), "application/pdf")},
        data={"gazette_no": "2024/01"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PENDING"
    assert data["rules_count"] == 1
    assert data["confidence"] == 0.94
    assert data["preview"]["gazette_no"] == "2024/01"


def test_upload_gazette_requires_admin(client, auth_headers):
    response = client.post(
        "/api/v1/gazette/upload",
        headers=auth_headers,
        files={"file": ("gazette.pdf", BytesIO(b"%PDF-1.4 test"), "application/pdf")},
        data={"gazette_no": "2024/NOADMIN"},
    )
    assert response.status_code == 403


def test_upload_gazette_rejects_non_pdf(client, admin_headers):
    response = client.post(
        "/api/v1/gazette/upload",
        headers=admin_headers,
        files={"file": ("gazette.txt", BytesIO(b"not pdf"), "text/plain")},
        data={"gazette_no": "2024/TXT"},
    )
    assert response.status_code == 400
    assert "Only PDF files are supported" in response.json()["detail"]


def test_upload_gazette_csv_success(client, admin_headers, db):
    csv_content = "\n".join(
        [
            "effective_date,rule_type,vehicle_type,fuel_type,engine_min,engine_max,customs_percent,excise_percent,vat_percent,pal_percent,cess_percent,apply_on,notes",
            "2024-02-01,VEHICLE_TAX,SEDAN,PETROL,1000,1500,25,50,15,7.5,0,CIF_PLUS_CUSTOMS,seeded manually",
        ]
    ).encode("utf-8")

    response = client.post(
        "/api/v1/gazette/upload-csv",
        headers=admin_headers,
        files={"file": ("gazette.csv", BytesIO(csv_content), "text/csv")},
        data={"gazette_no": "2024/CSV"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PENDING"
    assert data["rules_count"] == 1
    assert data["confidence"] == 1.0
    assert data["preview"]["source"] == "CSV_UPLOAD"
    assert data["preview"]["rules"][0]["vehicle_type"] == "SEDAN"

    saved = db.query(Gazette).filter(Gazette.gazette_no == "2024/CSV").first()
    assert saved is not None
    assert saved.effective_date.isoformat() == "2024-02-01"
    assert saved.raw_extracted["source"] == "CSV_UPLOAD"

    audit = next(
        (
            log
            for log in db.query(AuditLog).all()
            if (log.details or {}).get("gazette_no") == "2024/CSV"
        ),
        None,
    )
    assert audit is not None
    assert audit.details["source"] == "CSV_UPLOAD"


def test_upload_gazette_csv_rejects_non_csv(client, admin_headers):
    response = client.post(
        "/api/v1/gazette/upload-csv",
        headers=admin_headers,
        files={"file": ("gazette.pdf", BytesIO(b"%PDF-1.4 test"), "application/pdf")},
        data={"gazette_no": "2024/CSV-BAD"},
    )

    assert response.status_code == 400
    assert "Only CSV files are supported" in response.json()["detail"]


def test_upload_global_tax_parameters_catalog_csv_success(client, admin_headers, db):
    csv_content = "\n".join(
        [
            '"parameter_group,parameter_name,condition_or_type,value,unit,calculation_order,applicability_flag"',
            '"Valuation,Depreciation,<=1,95,%,0,used_only"',
            '"Valuation,Depreciation,>1-2,90,%,0,used_only"',
        ]
    ).encode("utf-8")

    response = client.post(
        "/api/v1/gazette/upload-global-tax-parameters-csv",
        headers=admin_headers,
        files={"file": ("global_tax_parameters.csv", BytesIO(csv_content), "text/csv")},
        data={"effective_date": "2025-01-01"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["dataset"] == "global_tax_parameters"
    assert data["uploaded_rows"] == 2
    assert data["superseded_rows"] == 0
    assert len(data["preview_rows"]) == 2
    assert data["preview_rows"][0]["parameter_group"] == "VALUATION"

    saved = db.query(GlobalTaxParameter).filter(GlobalTaxParameter.is_active.is_(True)).all()
    assert len(saved) == 2
    assert saved[0].effective_date.isoformat() == "2025-01-01"


def test_upload_hs_code_matrix_catalog_csv_supersedes_existing_rows(client, admin_headers, db):
    csv_content = "\n".join(
        [
            '"vehicle_type,fuel_type,age_condition,hs_code,capacity_min,capacity_max,capacity_unit,cid_pct,pal_pct,cess_pct,excise_unit_rate_lkr"',
            '"passenger_car,petrol,<=1,8703.21,0,1000,cc,20,0,6,2450"',
        ]
    ).encode("utf-8")

    first = client.post(
        "/api/v1/gazette/upload-hs-code-matrix-csv",
        headers=admin_headers,
        files={"file": ("hs_code_matrix.csv", BytesIO(csv_content), "text/csv")},
        data={"effective_date": "2025-01-01"},
    )
    second = client.post(
        "/api/v1/gazette/upload-hs-code-matrix-csv",
        headers=admin_headers,
        files={"file": ("hs_code_matrix.csv", BytesIO(csv_content), "text/csv")},
        data={"effective_date": "2025-02-01"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["superseded_rows"] == 1
    assert second.json()["preview_rows"][0]["vehicle_type"] == "PASSENGER_CAR"

    active_rows = db.query(HSCodeMatrixRule).filter(HSCodeMatrixRule.is_active.is_(True)).all()
    assert len(active_rows) == 1
    assert active_rows[0].version == 2
    assert active_rows[0].effective_date.isoformat() == "2025-02-01"


def test_edit_and_delete_catalog_rows(client, admin_headers, db):
    csv_content = "\n".join(
        [
            '"parameter_group,parameter_name,condition_or_type,value,unit,calculation_order,applicability_flag"',
            '"Valuation,Depreciation,<=1,95,%,0,used_only"',
        ]
    ).encode("utf-8")

    upload = client.post(
        "/api/v1/gazette/upload-global-tax-parameters-csv",
        headers=admin_headers,
        files={"file": ("global_tax_parameters.csv", BytesIO(csv_content), "text/csv")},
        data={"effective_date": "2025-01-01"},
    )
    assert upload.status_code == 200
    row_id = upload.json()["preview_rows"][0]["id"]

    update = client.patch(
        f"/api/v1/gazette/catalog/global_tax_parameters/{row_id}",
        headers=admin_headers,
        json={
            "values": {
                "parameter_group": "VALUATION",
                "parameter_name": "DEPRECIATION",
                "condition_or_type": "<=1",
                "value": 96,
                "unit": "%",
                "calculation_order": 0,
                "applicability_flag": "USED_ONLY",
                "effective_date": "2025-02-01",
            },
            "change_reason": "manual fix",
        },
    )
    assert update.status_code == 200
    assert update.json()["value"] == 96.0
    new_row_id = update.json()["id"]

    delete = client.delete(
        f"/api/v1/gazette/catalog/global_tax_parameters/{new_row_id}",
        headers=admin_headers,
        params={"change_reason": "remove bad row"},
    )
    assert delete.status_code == 200

    active_rows = db.query(GlobalTaxParameter).filter(GlobalTaxParameter.is_active.is_(True)).all()
    assert active_rows == []


def test_upload_gazette_size_limit(client, admin_headers, mocker):
    mocker.patch("app.modules.gazette.routes.settings.MAX_GAZETTE_SIZE_MB", 0)
    response = client.post(
        "/api/v1/gazette/upload",
        headers=admin_headers,
        files={"file": ("gazette.pdf", BytesIO(b"%PDF-1.4 test"), "application/pdf")},
        data={"gazette_no": "2024/LARGE"},
    )
    assert response.status_code == 413


def test_upload_gazette_fallback_manual_review(client, admin_headers, db, mocker):
    mocker.patch(
        "app.modules.gazette.routes.document_ai_service.parse_gazette_pdf",
        new=AsyncMock(return_value={"text": "raw", "tables": [], "pages": 1, "confidence": 0.61}),
    )
    mocker.patch(
        "app.modules.gazette.routes.gemini_service.structure_gazette",
        new=AsyncMock(side_effect=RuntimeError("invalid json")),
    )

    response = client.post(
        "/api/v1/gazette/upload",
        headers=admin_headers,
        files={"file": ("gazette.pdf", BytesIO(b"%PDF-1.4 test"), "application/pdf")},
        data={"gazette_no": "2024/FALLBACK"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "NEEDS_MANUAL_REVIEW"
    assert data["rules_count"] == 0
    assert "message" in data

    saved = db.query(Gazette).filter(Gazette.gazette_no == "2024/FALLBACK").first()
    assert saved is not None
    assert saved.status == "PENDING"


def test_upload_gazette_uses_ocr_fallback_when_gemini_fails(client, admin_headers, db, mocker):
    electric_text = """
    Effective date 01/02/2025
    8703.80.11 Electric auto-trishaws. For vehicles not more than one year old: Rs.18,100/- per kW.
    For vehicles more than one year old but not more than two years old: Rs.24,100/- per kW.
    8703.80.12 For vehicles more than two years old: Rs.36,200/- per kW.
    """
    mocker.patch(
        "app.modules.gazette.routes.document_ai_service.parse_gazette_pdf",
        new=AsyncMock(
            return_value={"text": electric_text, "tables": [], "pages": 2, "confidence": 0.97}
        ),
    )
    mocker.patch(
        "app.modules.gazette.routes.gemini_service.structure_gazette",
        new=AsyncMock(side_effect=RuntimeError("504 timeout")),
    )

    response = client.post(
        "/api/v1/gazette/upload",
        headers=admin_headers,
        files={"file": ("electric.pdf", BytesIO(b"%PDF-1.4 test"), "application/pdf")},
        data={"gazette_no": "2025/ELECTRIC-FALLBACK"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PENDING"
    assert data["rules_count"] == 3
    assert "OCR fallback parser" in (data.get("message") or "")

    saved = db.query(Gazette).filter(Gazette.gazette_no == "2025/ELECTRIC-FALLBACK").first()
    assert saved is not None
    assert len(saved.raw_extracted["rules"]) == 3


def test_upload_gazette_prefers_ocr_fallback_when_it_extracts_more_rules(
    client, admin_headers, db, mocker
):
    electric_text = """
    Effective date 01/02/2025
    8703.80.11 Electric auto-trishaws. For vehicles not more than one year old: Rs.18,100/- per kW.
    For vehicles more than one year old but not more than two years old: Rs.24,100/- per kW.
    8703.80.12 For vehicles more than two years old: Rs.36,200/- per kW.
    """
    mocker.patch(
        "app.modules.gazette.routes.document_ai_service.parse_gazette_pdf",
        new=AsyncMock(
            return_value={"text": electric_text, "tables": [], "pages": 2, "confidence": 0.97}
        ),
    )
    mocker.patch(
        "app.modules.gazette.routes.gemini_service.structure_gazette",
        new=AsyncMock(
            return_value={
                "gazette_no": "2025/ELECTRIC-PARTIAL",
                "effective_date": "2025-02-01",
                "rules": [
                    {
                        "vehicle_type": "OTHER",
                        "fuel_type": "ELECTRIC",
                        "category_code": "ELECTRIC_AUTO_TRISHAW",
                        "excise_per_kw_amount": 18100,
                    }
                ],
            }
        ),
    )

    response = client.post(
        "/api/v1/gazette/upload",
        headers=admin_headers,
        files={"file": ("electric.pdf", BytesIO(b"%PDF-1.4 test"), "application/pdf")},
        data={"gazette_no": "2025/ELECTRIC-PARTIAL"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PENDING"
    assert data["rules_count"] == 3


def test_parse_ocr_to_rules_extracts_clean_electric_rule_matrix():
    electric_text = """
    Effective date 31/01/2025
    8703.80.11 Electric auto-trishaws. For vehicles not more than one year old: Rs.18,100/- per kW.
    For vehicles more than one year old but not more than two years old: Rs.24,100/- per kW.
    8703.80.12 For vehicles more than two years old: Rs.36,200/- per kW.
    8703.80.21 Passenger vehicles (solar electric). For vehicles not more than one year old: Rs.18,100/- per kW.
    For vehicles more than one year old but not more than three years old: Rs.36,200/- per kW.
    8703.80.22 For vehicles more than three years old: Rs.48,300/- per kW.
    8703.80.31 Capacity of motors not exceeding 50kW. For vehicles not more than one year old: Rs.18,100/- per kW.
    For vehicles more than one year old but not more than three years old: Rs.36,200/- per kW.
    8703.80.32 Capacity of motors exceeding 50kW, but not exceeding 100kW. For vehicles not more than one year old: Rs.24,100/- per kW.
    For vehicles more than one year old but not more than three years old: Rs.36,200/- per kW.
    8703.80.33 Capacity of motors exceeding 100kW, but not exceeding 200kW. For vehicles not more than one year old: Rs.36,200/- per kW.
    For vehicles more than one year old but not more than three years old: Rs.60,400/- per kW.
    8703.80.34 Capacity of motors exceeding 200kW. For vehicles not more than one year old: Rs.96,600/- per kW.
    For vehicles more than one year old but not more than three years old: Rs.132,800/- per kW.
    8703.80.41 Capacity of motors not exceeding 50kW. For vehicles more than three years old: Rs.48,300/- per kW.
    8703.80.42 Capacity of motors exceeding 50kW, but not exceeding 100kW. For vehicles more than three years old: Rs.72,400/- per kW.
    8703.80.43 Capacity of motors exceeding 100kW, but not exceeding 200kW. For vehicles more than three years old: Rs.108,700/- per kW.
    8703.80.44 Capacity of motors exceeding 200kW. For vehicles more than three years old: Rs.144,900/- per kW.
    8703.80.51 Capacity of motors not exceeding 50kW. For vehicles not more than one year old: Rs.18,100/- per kW.
    For vehicles more than one year old but not more than three years old: Rs.36,200/- per kW.
    8703.80.52 Capacity of motors exceeding 50kW, but not exceeding 100kW. For vehicles not more than one year old: Rs.24,100/- per kW.
    For vehicles more than one year old but not more than three years old: Rs.36,200/- per kW.
    8703.80.53 Capacity of motors exceeding 100kW, but not exceeding 200kW. For vehicles not more than one year old: Rs.36,200/- per kW.
    For vehicles more than one year old but not more than three years old: Rs.60,400/- per kW.
    8703.80.54 Capacity of motors exceeding 200kW. For vehicles not more than one year old: Rs.96,600/- per kW.
    For vehicles more than one year old but not more than three years old: Rs.132,800/- per kW.
    8703.80.61 Capacity of motors not exceeding 50kW. For vehicles more than three years old: Rs.48,300/- per kW.
    8703.80.62 Capacity of motors exceeding 50kW, but not exceeding 100kW. For vehicles more than three years old: Rs.72,400/- per kW.
    8703.80.63 Capacity of motors exceeding 100kW, but not exceeding 200kW. For vehicles more than three years old: Rs.108,700/- per kW.
    8703.80.64 Capacity of motors exceeding 200kW. For vehicles more than three years old: Rs.144,900/- per kW.
    8703.80.71 Passenger vehicles (electric). For vehicles not more than one year old: Rs.96,600/- per kW.
    For vehicles more than one year old but not more than three years old: Rs.132,800/- per kW.
    8703.80.72 For vehicles more than three years old: Rs.144,900/- per kW.
    8704.60.10 Electric auto-trishaws for goods. For vehicles not more than five years old: Rs.18,100/- per kW.
    8704.60.20 Electric auto-trishaws for goods. For vehicles more than five years old: Rs.18,100/- per kW.
    8704.60.31 Capacity of motors not exceeding 50kW. For vehicles not more than five years old: Rs.18,100/- per kW.
    8704.60.32 Capacity of motors exceeding 50kW, but not exceeding 100kW. For vehicles not more than five years old: Rs.24,100/- per kW.
    8704.60.33 Capacity of motors exceeding 100kW, but not exceeding 200kW. For vehicles not more than five years old: Rs.60,400/- per kW.
    8704.60.34 Capacity of motors exceeding 200kW. For vehicles not more than five years old: Rs.96,600/- per kW.
    8704.60.41 Capacity of motors not exceeding 50kW. For vehicles more than five years old: Rs.48,300/- per kW.
    8704.60.42 Capacity of motors exceeding 50kW, but not exceeding 100kW. For vehicles more than five years old: Rs.72,400/- per kW.
    8704.60.43 Capacity of motors exceeding 100kW, but not exceeding 200kW. For vehicles more than five years old: Rs.108,700/- per kW.
    8704.60.44 Capacity of motors exceeding 200kW. For vehicles more than five years old: Rs.144,900/- per kW.
    """

    structured = parse_ocr_to_rules(electric_text, "2025/ELECTRIC-FULL")

    assert structured is not None
    assert structured["effective_date"] == "2025-01-31"
    assert len(structured["rules"]) == 43

    category_counts = {}
    for rule in structured["rules"]:
        category_counts[rule["category_code"]] = category_counts.get(rule["category_code"], 0) + 1
    assert category_counts == {
        "ELECTRIC_AUTO_TRISHAW": 3,
        "PASSENGER_VEHICLE_SOLAR_ELECTRIC": 3,
        "PASSENGER_VEHICLE_BEV": 12,
        "PASSENGER_VEHICLE_RANGE_EXTENDED_EV": 12,
        "PASSENGER_VEHICLE_ELECTRIC_OTHER": 3,
        "ELECTRIC_AUTO_TRISHAW_GOODS": 2,
        "GOODS_VEHICLE_ELECTRIC": 8,
    }

    bev_rules = [
        rule for rule in structured["rules"] if rule["category_code"] == "PASSENGER_VEHICLE_BEV"
    ]
    assert len(bev_rules) == 12
    assert {
        (
            rule["power_min_kw"],
            rule["power_max_kw"],
            rule["age_min_years"],
            rule["age_max_years"],
            rule["excise_rate"],
        )
        for rule in bev_rules
    } == {
        (0.0, 50.0, 0.0, 1.0, 18100.0),
        (0.0, 50.0, 1.01, 3.0, 36200.0),
        (0.0, 50.0, 3.01, 999.0, 48300.0),
        (50.01, 100.0, 0.0, 1.0, 24100.0),
        (50.01, 100.0, 1.01, 3.0, 36200.0),
        (50.01, 100.0, 3.01, 999.0, 72400.0),
        (100.01, 200.0, 0.0, 1.0, 36200.0),
        (100.01, 200.0, 1.01, 3.0, 60400.0),
        (100.01, 200.0, 3.01, 999.0, 108700.0),
        (200.01, 999999.0, 0.0, 1.0, 96600.0),
        (200.01, 999999.0, 1.01, 3.0, 132800.0),
        (200.01, 999999.0, 3.01, 999.0, 144900.0),
    }

    assert all(
        rule["power_min_kw"] == 0.0
        for rule in structured["rules"]
        if rule["category_code"] == "ELECTRIC_AUTO_TRISHAW"
    )
    assert all(
        rule["power_max_kw"] == 999999.0
        for rule in structured["rules"]
        if rule["category_code"] == "ELECTRIC_AUTO_TRISHAW"
    )
    assert all(rule["hs_code"] for rule in structured["rules"])
    assert all(
        set(rule.keys())
        == {
            "category_code",
            "fuel_type",
            "power_min_kw",
            "power_max_kw",
            "age_min_years",
            "age_max_years",
            "excise_type",
            "excise_rate",
            "hs_code",
        }
        for rule in structured["rules"]
    )

    match_bev_120kw_age_2 = [
        rule
        for rule in bev_rules
        if rule["power_min_kw"] <= 120 <= rule["power_max_kw"]
        and rule["age_min_years"] <= 2 <= rule["age_max_years"]
    ]
    match_bev_40kw_age_4 = [
        rule
        for rule in bev_rules
        if rule["power_min_kw"] <= 40 <= rule["power_max_kw"]
        and rule["age_min_years"] <= 4 <= rule["age_max_years"]
    ]
    assert len(match_bev_120kw_age_2) == 1
    assert match_bev_120kw_age_2[0]["power_min_kw"] == 100.01
    assert match_bev_120kw_age_2[0]["power_max_kw"] == 200.0
    assert match_bev_120kw_age_2[0]["age_min_years"] == 1.01
    assert match_bev_120kw_age_2[0]["age_max_years"] == 3.0
    assert len(match_bev_40kw_age_4) == 1
    assert match_bev_40kw_age_4[0]["power_min_kw"] == 0.0
    assert match_bev_40kw_age_4[0]["power_max_kw"] == 50.0
    assert match_bev_40kw_age_4[0]["age_min_years"] == 3.01
    assert match_bev_40kw_age_4[0]["age_max_years"] == 999.0


def test_sanitize_electric_vehicle_rules_rebuilds_canonical_matrix_from_dirty_rows():
    dirty_rules = [
        {
            "rule_type": "VEHICLE_TAX",
            "vehicle_type": "OTHER",
            "fuel_type": "ELECTRIC",
            "category_code": "ELECTRIC_AUTO_TRISHAW",
            "hs_code": "8703.80.31",
            "name": "CUSTOMS_SURCHARGE",
            "applies_to": "CUSTOMS_DUTY",
            "surcharge_percent": 0,
            "threshold_value": None,
            "luxury_tax_threshold": None,
            "luxury_tax_percent": None,
            "age_years_min": 2.01,
            "age_years_max": None,
            "excise_per_kw_amount": 18100,
            "notes": "HS Code: 8703.80.11. Electric auto-trishaws, not more than one year old.",
        },
        {
            "rule_type": "VEHICLE_TAX",
            "vehicle_type": "OTHER",
            "fuel_type": "ELECTRIC",
            "category_code": "ELECTRIC_AUTO_TRISHAW",
            "hs_code": "8703.80.31",
            "name": "CUSTOMS_SURCHARGE",
            "applies_to": "CUSTOMS_DUTY",
            "surcharge_percent": 0,
            "age_years_min": 2.01,
            "age_years_max": None,
            "excise_per_kw_amount": 24100,
            "notes": "HS Code: 8703.80.11. Electric auto-trishaws, more than one year old but not more than two years old.",
        },
        {
            "rule_type": "VEHICLE_TAX",
            "vehicle_type": "OTHER",
            "fuel_type": "ELECTRIC",
            "category_code": "ELECTRIC_AUTO_TRISHAW",
            "hs_code": "8703.80.31",
            "name": "CUSTOMS_SURCHARGE",
            "applies_to": "CUSTOMS_DUTY",
            "surcharge_percent": 0,
            "age_years_min": 2.01,
            "age_years_max": None,
            "excise_per_kw_amount": 36200,
            "notes": "HS Code: 8703.80.12. Electric auto-trishaws, more than two years old.",
        },
    ]

    sanitized = sanitize_electric_vehicle_rules(dirty_rules)

    assert sanitized is not None
    assert len(sanitized) == 3
    assert {rule["hs_code"] for rule in sanitized} == {"8703.80.11", "8703.80.12"}
    assert all(rule["excise_type"] == "PER_KW" for rule in sanitized)
    assert all("name" not in rule for rule in sanitized)
    assert all("applies_to" not in rule for rule in sanitized)
    assert all("excise_per_kw_amount" not in rule for rule in sanitized)
    assert {
        (
            rule["power_min_kw"],
            rule["power_max_kw"],
            rule["age_min_years"],
            rule["age_max_years"],
            rule["excise_rate"],
        )
        for rule in sanitized
    } == {
        (0.0, 999999.0, 0.0, 1.0, 18100.0),
        (0.0, 999999.0, 1.01, 2.0, 24100.0),
        (0.0, 999999.0, 2.01, 999.0, 36200.0),
    }


def test_sanitize_electric_vehicle_rules_preserves_explicit_single_rule_shape():
    sanitized = sanitize_electric_vehicle_rules(
        [
            {
                "rule_type": "VEHICLE_TAX",
                "category_code": "PASSENGER_VEHICLE_BEV",
                "fuel_type": "ELECTRIC",
                "power_min_kw": 50.01,
                "power_max_kw": 100.0,
                "age_min_years": 1.01,
                "age_max_years": 3.0,
                "excise_type": "PER_KW",
                "excise_rate": 36200.0,
                "hs_code": "8703.80.32",
            }
        ]
    )

    assert sanitized == [
        {
            "category_code": "PASSENGER_VEHICLE_BEV",
            "fuel_type": "ELECTRIC",
            "power_min_kw": 50.01,
            "power_max_kw": 100.0,
            "age_min_years": 1.01,
            "age_max_years": 3.0,
            "excise_type": "PER_KW",
            "excise_rate": 36200.0,
            "hs_code": "8703.80.32",
        }
    ]


def test_upload_gazette_document_ai_auth_failure_becomes_manual_review(
    client, admin_headers, db, mocker
):
    mocker.patch(
        "app.modules.gazette.routes.document_ai_service.parse_gazette_pdf",
        new=AsyncMock(
            side_effect=RuntimeError(
                "Document AI credentials are missing. Configure "
                "GOOGLE_APPLICATION_CREDENTIALS_PATH or GOOGLE_SERVICE_ACCOUNT_JSON."
            )
        ),
    )

    response = client.post(
        "/api/v1/gazette/upload",
        headers=admin_headers,
        files={"file": ("gazette.pdf", BytesIO(b"%PDF-1.4 test"), "application/pdf")},
        data={"gazette_no": "2024/AUTHFAIL"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "NEEDS_MANUAL_REVIEW"
    assert "Document AI credentials are missing" in data["message"]

    saved = db.query(Gazette).filter(Gazette.gazette_no == "2024/AUTHFAIL").first()
    assert saved is not None
    assert saved.status == "PENDING"


def test_upload_gazette_reprocesses_existing_pending_record(client, admin_headers, db, mocker):
    existing = Gazette(
        gazette_no="2026/03",
        effective_date=None,
        raw_extracted={"rules": []},
        status="PENDING",
    )
    db.add(existing)
    db.commit()
    db.refresh(existing)

    mocker.patch(
        "app.modules.gazette.routes.document_ai_service.parse_gazette_pdf",
        new=AsyncMock(
            return_value={
                "text": "Gazette text",
                "tables": [],
                "pages": 1,
                "confidence": 0.91,
            }
        ),
    )
    mocker.patch(
        "app.modules.gazette.routes.gemini_service.structure_gazette",
        new=AsyncMock(
            return_value={
                "gazette_no": "2026/03",
                "effective_date": "2026-03-19",
                "rules": [
                    {
                        "vehicle_type": "SEDAN",
                        "fuel_type": "PETROL",
                        "engine_min": 1000,
                        "engine_max": 1500,
                        "customs_percent": 25.0,
                        "excise_percent": 50.0,
                        "vat_percent": 15.0,
                        "pal_percent": 7.5,
                        "cess_percent": 0.0,
                        "apply_on": "CIF_PLUS_CUSTOMS",
                    }
                ],
            }
        ),
    )

    response = client.post(
        "/api/v1/gazette/upload",
        headers=admin_headers,
        files={"file": ("gazette.pdf", BytesIO(b"%PDF-1.4 test"), "application/pdf")},
        data={"gazette_no": "2026/03"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["gazette_id"] == str(existing.id)
    assert data["rules_count"] == 1
    assert data["status"] == "PENDING"

    db.refresh(existing)
    assert existing.effective_date.isoformat() == "2026-03-19"
    assert len(existing.raw_extracted["rules"]) == 1


def test_upload_gazette_creates_uploaded_audit_log(client, admin_headers, db, mocker):
    mocker.patch(
        "app.modules.gazette.routes.document_ai_service.parse_gazette_pdf",
        new=AsyncMock(
            return_value={"text": "Gazette text", "tables": [], "pages": 1, "confidence": 0.88}
        ),
    )
    mocker.patch(
        "app.modules.gazette.routes.gemini_service.structure_gazette",
        new=AsyncMock(
            return_value={
                "gazette_no": "2024/AUDIT",
                "effective_date": "2024-02-01",
                "rules": [],
            }
        ),
    )

    response = client.post(
        "/api/v1/gazette/upload",
        headers=admin_headers,
        files={"file": ("gazette.pdf", BytesIO(b"%PDF-1.4 test"), "application/pdf")},
        data={"gazette_no": "2024/AUDIT"},
    )

    assert response.status_code == 200
    audit = (
        db.query(AuditLog).filter(AuditLog.event_type == AuditEventType.GAZETTE_UPLOADED).first()
    )
    assert audit is not None
    assert audit.details["gazette_no"] == "2024/AUDIT"


def test_approve_gazette_creates_audit_logs(client, db, admin_headers, admin_user):
    gazette = Gazette(
        gazette_no="2024/APPROVE",
        effective_date=None,
        raw_extracted={
            "effective_date": "2024-02-01",
            "rules": [
                {
                    "vehicle_type": "SEDAN",
                    "fuel_type": "PETROL",
                    "engine_min": 1000,
                    "engine_max": 1500,
                    "customs_percent": 25,
                    "excise_percent": 50,
                    "vat_percent": 15,
                    "pal_percent": 7.5,
                    "cess_percent": 0,
                    "apply_on": "CIF_PLUS_CUSTOMS",
                }
            ],
        },
        status="PENDING",
        uploaded_by=admin_user.id,
    )
    db.add(gazette)
    db.commit()
    db.refresh(gazette)

    response = client.post(f"/api/v1/gazette/{gazette.id}/approve", headers=admin_headers)

    assert response.status_code == 200
    db.refresh(gazette)
    assert gazette.status == "APPROVED"

    event_types = {
        audit.event_type
        for audit in db.query(AuditLog).filter(AuditLog.admin_id == admin_user.id).all()
    }
    assert AuditEventType.GAZETTE_APPROVED in event_types
    assert AuditEventType.TAX_RULES_ACTIVATED in event_types


def test_approve_gazette_merges_rules_from_multiple_approved_gazettes(
    client, db, admin_headers, admin_user
):
    customs_gazette = Gazette(
        gazette_no="2024/CUSTOMS",
        effective_date=None,
        raw_extracted={
            "effective_date": "2024-02-01",
            "rules": [
                {
                    "vehicle_type": "SEDAN",
                    "fuel_type": "PETROL",
                    "engine_min": 1000,
                    "engine_max": 1500,
                    "customs_percent": 25,
                    "apply_on": "CIF_PLUS_CUSTOMS",
                }
            ],
        },
        status="PENDING",
        uploaded_by=admin_user.id,
    )
    surcharge_gazette = Gazette(
        gazette_no="2024/SURCHARGE",
        effective_date=None,
        raw_extracted={
            "effective_date": "2024-03-01",
            "rules": [
                {
                    "vehicle_type": "SEDAN",
                    "fuel_type": "PETROL",
                    "engine_min": 1000,
                    "engine_max": 1500,
                    "excise_percent": 50,
                    "vat_percent": 15,
                    "pal_percent": 7.5,
                    "cess_percent": 5,
                }
            ],
        },
        status="PENDING",
        uploaded_by=admin_user.id,
    )
    db.add(customs_gazette)
    db.add(surcharge_gazette)
    db.commit()
    db.refresh(customs_gazette)
    db.refresh(surcharge_gazette)

    response_one = client.post(
        f"/api/v1/gazette/{customs_gazette.id}/approve", headers=admin_headers
    )
    response_two = client.post(
        f"/api/v1/gazette/{surcharge_gazette.id}/approve", headers=admin_headers
    )

    assert response_one.status_code == 200
    assert response_two.status_code == 200

    active_rules = db.query(TaxRule).filter(TaxRule.is_active.is_(True)).all()
    assert len(active_rules) == 1
    rule = active_rules[0]
    assert float(rule.customs_percent) == 25.0
    assert float(rule.excise_percent) == 50.0
    assert float(rule.vat_percent) == 15.0
    assert float(rule.pal_percent) == 7.5
    assert float(rule.cess_percent) == 5.0
    assert rule.apply_on == "CIF_PLUS_CUSTOMS"


def test_approve_gazette_rejects_overlapping_electric_vehicle_rules(
    client, db, admin_headers, admin_user
):
    gazette = Gazette(
        gazette_no="2025/ELECTRIC-OVERLAP",
        effective_date=None,
        raw_extracted={
            "effective_date": "2025-02-01",
            "rules": [
                {
                    "category_code": "PASSENGER_VEHICLE_BEV",
                    "fuel_type": "ELECTRIC",
                    "power_min_kw": 100,
                    "power_max_kw": 200,
                    "age_min_years": 1,
                    "age_max_years": 3,
                    "excise_type": "PER_KW",
                    "excise_rate": 60400,
                    "hs_code": "9999.99.91",
                },
                {
                    "category_code": "PASSENGER_VEHICLE_BEV",
                    "fuel_type": "ELECTRIC",
                    "power_min_kw": 150,
                    "power_max_kw": 220,
                    "age_min_years": 2,
                    "age_max_years": 4,
                    "excise_type": "PER_KW",
                    "excise_rate": 70000,
                    "hs_code": "9999.99.92",
                },
            ],
        },
        status="PENDING",
        uploaded_by=admin_user.id,
    )
    db.add(gazette)
    db.commit()
    db.refresh(gazette)

    response = client.post(f"/api/v1/gazette/{gazette.id}/approve", headers=admin_headers)

    assert response.status_code == 400
    assert "overlap" in response.json()["detail"].lower()


def test_approve_gazette_rejects_vehicle_tax_rule_with_missing_ranges(
    client, db, admin_headers, admin_user
):
    gazette = Gazette(
        gazette_no="2025/ELECTRIC-MISSING-RANGES",
        effective_date=None,
        raw_extracted={
            "effective_date": "2025-02-01",
            "rules": [
                {
                    "category_code": "PASSENGER_VEHICLE_BEV",
                    "fuel_type": "ELECTRIC",
                    "excise_type": "PER_KW",
                    "excise_rate": 24100,
                    "hs_code": "9999.99.91",
                }
            ],
        },
        status="PENDING",
        uploaded_by=admin_user.id,
    )
    db.add(gazette)
    db.commit()
    db.refresh(gazette)

    response = client.post(f"/api/v1/gazette/{gazette.id}/approve", headers=admin_headers)

    assert response.status_code == 400
    assert "missing power or age ranges" in response.json()["detail"].lower()


def test_approve_gazette_rejects_duplicate_hs_code_with_same_ranges(
    client, db, admin_headers, admin_user
):
    gazette = Gazette(
        gazette_no="2025/ELECTRIC-DUPLICATE-HS",
        effective_date=None,
        raw_extracted={
            "effective_date": "2025-02-01",
            "rules": [
                {
                    "category_code": "PASSENGER_VEHICLE_BEV",
                    "fuel_type": "ELECTRIC",
                    "power_min_kw": 50.01,
                    "power_max_kw": 100.0,
                    "age_min_years": 1.01,
                    "age_max_years": 3.0,
                    "excise_type": "PER_KW",
                    "excise_rate": 36200,
                    "hs_code": "9999.99.91",
                },
                {
                    "category_code": "PASSENGER_VEHICLE_BEV",
                    "fuel_type": "ELECTRIC",
                    "power_min_kw": 50.01,
                    "power_max_kw": 100.0,
                    "age_min_years": 1.01,
                    "age_max_years": 3.0,
                    "excise_type": "PER_KW",
                    "excise_rate": 36200,
                    "hs_code": "9999.99.91",
                },
            ],
        },
        status="PENDING",
        uploaded_by=admin_user.id,
    )
    db.add(gazette)
    db.commit()
    db.refresh(gazette)

    response = client.post(f"/api/v1/gazette/{gazette.id}/approve", headers=admin_headers)

    assert response.status_code == 400
    assert "duplicate vehicle tax rule" in response.json()["detail"].lower()


def test_update_gazette_review_persists_manual_corrections(client, db, admin_headers, admin_user):
    gazette = Gazette(
        gazette_no="2024/MANUAL",
        effective_date=None,
        raw_extracted={"text": "raw scan", "tables": [], "rules": []},
        status="PENDING",
        uploaded_by=admin_user.id,
    )
    db.add(gazette)
    db.commit()
    db.refresh(gazette)

    response = client.patch(
        f"/api/v1/gazette/{gazette.id}",
        headers=admin_headers,
        json={
            "effective_date": "2024-02-01",
            "rules": [
                {
                    "vehicle_type": "Passenger Vehicle (BEV)",
                    "fuel_type": "Electric",
                    "category_code": "PASSENGER_VEHICLE_BEV",
                    "hs_code": "8703.80.32",
                    "engine_min": 0,
                    "engine_max": 999999,
                    "power_kw_min": 50.01,
                    "power_kw_max": 100,
                    "age_years_min": 0,
                    "age_years_max": 3,
                    "customs_percent": 0,
                    "excise_percent": 0,
                    "excise_per_kw_amount": 24100,
                    "vat_percent": 15,
                    "pal_percent": 0,
                    "cess_percent": 0,
                    "apply_on": "cif",
                    "notes": "corrected manually",
                }
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["effective_date"] == "2024-02-01"
    assert data["rules_count"] == 1
    assert data["preview"]["rules"][0] == {
        "category_code": "PASSENGER_VEHICLE_BEV",
        "fuel_type": "ELECTRIC",
        "power_min_kw": 50.01,
        "power_max_kw": 100.0,
        "age_min_years": 0.0,
        "age_max_years": 3.0,
        "excise_type": "PER_KW",
        "excise_rate": 24100.0,
        "hs_code": "8703.80.32",
    }


def test_reject_gazette_creates_audit_log(client, db, admin_headers, admin_user):
    gazette = Gazette(
        gazette_no="2024/REJECT",
        effective_date=None,
        raw_extracted={"rules": []},
        status="PENDING",
        uploaded_by=admin_user.id,
    )
    db.add(gazette)
    db.commit()
    db.refresh(gazette)

    response = client.post(
        f"/api/v1/gazette/{gazette.id}/reject",
        headers=admin_headers,
        json={"reason": "Rejected because the extracted values are inconsistent"},
    )

    assert response.status_code == 200
    db.refresh(gazette)
    assert gazette.status == "REJECTED"
    assert gazette.rejection_reason == "Rejected because the extracted values are inconsistent"

    audit = (
        db.query(AuditLog).filter(AuditLog.event_type == AuditEventType.GAZETTE_REJECTED).first()
    )
    assert audit is not None
    assert audit.details["gazette_no"] == "2024/REJECT"


async def test_gemini_structure_gazette_merges_long_document_chunks(mocker):
    service = GeminiService()
    mocker.patch.object(service, "_ensure_model")

    raw_text = "\n".join(
        [
            "8703.80.11 Electric auto-trishaw passenger not more than one year old",
            "A" * 4600,
            "8703.80.31 Passenger vehicle BEV not more than one year old and <=50kW",
            "B" * 4600,
            "8704.60.10 Electric goods auto-trishaw not more than five years old",
            "C" * 4600,
        ]
    )

    chunk_responses = [
        {
            "gazette_no": "2025/01",
            "effective_date": "2025-02-01",
            "rules": [
                {
                    "vehicle_type": "OTHER",
                    "fuel_type": "ELECTRIC",
                    "category_code": "ELECTRIC_AUTO_TRISHAW",
                    "excise_per_kw_amount": 18100,
                }
            ],
        },
        {
            "gazette_no": "2025/01",
            "effective_date": "2025-02-01",
            "rules": [
                {
                    "vehicle_type": "ELECTRIC",
                    "fuel_type": "ELECTRIC",
                    "category_code": "PASSENGER_VEHICLE_BEV",
                    "power_kw_min": 0,
                    "power_kw_max": 50,
                    "excise_per_kw_amount": 18100,
                }
            ],
        },
        {
            "gazette_no": "2025/01",
            "effective_date": "2025-02-01",
            "rules": [
                {
                    "vehicle_type": "TRUCK",
                    "fuel_type": "ELECTRIC",
                    "category_code": "ELECTRIC_AUTO_TRISHAW_GOODS",
                    "excise_per_kw_amount": 18100,
                }
            ],
        },
    ]

    async def fake_generate(_prompt, _genai):
        response = chunk_responses.pop(0)
        return SimpleNamespace(text=str(response).replace("'", '"'))

    mocker.patch.object(service, "_generate_structured_content", side_effect=fake_generate)

    result = await service.structure_gazette(raw_text, [], "2025/01")

    assert result["effective_date"] == "2025-02-01"
    assert len(result["rules"]) == 3
    assert {rule["category_code"] for rule in result["rules"]} == {
        "ELECTRIC_AUTO_TRISHAW",
        "PASSENGER_VEHICLE_BEV",
        "ELECTRIC_AUTO_TRISHAW_GOODS",
    }


def test_gemini_build_structuring_chunks_splits_hs_code_sections():
    service = GeminiService()
    raw_text = "\n".join(
        [
            "8703.80.11 Electric auto-trishaw passenger not more than one year old",
            "A" * 4600,
            "8703.80.31 Passenger vehicle BEV not more than one year old and <=50kW",
            "B" * 4600,
            "8704.60.10 Electric goods auto-trishaw not more than five years old",
            "C" * 4600,
        ]
    )

    chunks = service._build_structuring_chunks(raw_text, [])

    assert len(chunks) >= 2
    assert "8703.80.11" in chunks[0][0]
    assert any("8704.60.10" in chunk_text for chunk_text, _ in chunks)
