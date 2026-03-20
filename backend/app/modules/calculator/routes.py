"""Tax calculator endpoints."""

from __future__ import annotations

import logging

from app.core.database import get_db
from app.services.tax_calculator import (
    InsufficientVehicleDataError,
    NoTaxRuleError,
    calculate_tax,
)
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

router = APIRouter(prefix="/calculate", tags=["Calculator"])
logger = logging.getLogger(__name__)


class TaxCalculationRequest(BaseModel):
    """Tax calculation request payload."""

    vehicle_type: str = Field(..., description="SEDAN, SUV, TRUCK, VAN, MOTORCYCLE, ELECTRIC")
    fuel_type: str = Field(..., description="PETROL, DIESEL, ELECTRIC, HYBRID")
    engine_cc: int = Field(..., ge=0, le=10000, description="Engine capacity in cc")
    power_kw: float | None = Field(None, ge=0, description="Motor power in kW, if applicable")
    vehicle_age_years: float | None = Field(
        None, ge=0, description="Vehicle age in years, if rule matching requires it"
    )
    category_code: str | None = Field(
        None, description="Optional sub-category such as PASSENGER_VEHICLE_BEV"
    )
    cif_value: float = Field(..., gt=0, description="CIF value in LKR")


class TaxCalculationResponse(BaseModel):
    """Tax calculation response payload."""

    cif_value: float
    customs_duty: float
    surcharge: float
    excise_duty: float
    cess: float
    vat: float
    pal: float
    luxury_tax: float
    total_duty: float
    total_landed_cost: float
    effective_rate_percent: float
    rule_used: dict


@router.post("/tax", response_model=TaxCalculationResponse)
async def calculate_vehicle_tax(
    request: TaxCalculationRequest, db: Session = Depends(get_db)
) -> TaxCalculationResponse:
    """Calculate import tax using active DB rules."""
    try:
        result = calculate_tax(
            db=db,
            vehicle_type=request.vehicle_type,
            fuel_type=request.fuel_type,
            engine_cc=request.engine_cc,
            cif_value=request.cif_value,
            power_kw=request.power_kw,
            vehicle_age_years=request.vehicle_age_years,
            category_codes=[request.category_code] if request.category_code else None,
        )
        return TaxCalculationResponse(**result)
    except NoTaxRuleError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NO_TAX_RULE_FOUND",
                "message": str(exc),
                "suggestion": (
                    "This vehicle configuration may not be currently supported. "
                    "Contact admin or check available tax rules."
                ),
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_PARAMETERS", "message": str(exc)},
        ) from exc
    except InsufficientVehicleDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "MISSING_VEHICLE_DATA", "message": str(exc)},
        ) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Tax calculation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "CALCULATION_FAILED",
                "message": "An error occurred during tax calculation",
            },
        ) from exc
