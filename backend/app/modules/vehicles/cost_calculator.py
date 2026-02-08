# backend/app/modules/vehicles/cost_calculator.py

"""
Vehicle import cost calculator for Sri Lanka.

Calculates total landed cost including:
- Vehicle price (JPY to LKR conversion)
- Shipping costs
- Customs duties (based on engine CC and fuel type)
- Excise duty
- VAT (15%)
- Cess
- Port charges
- Service fees
"""

from decimal import Decimal
from typing import Dict

from .models import FuelType, Vehicle

# ============================================================================
# EXCHANGE RATE
# ============================================================================

# Default JPY to LKR exchange rate (update this regularly in production)
DEFAULT_JPY_TO_LKR = Decimal("2.25")  # 1 JPY = 2.25 LKR (approximate)


# ============================================================================
# SHIPPING COSTS (Based on vehicle type)
# ============================================================================


def calculate_shipping_cost(vehicle: Vehicle) -> Decimal:
    """
    Calculate shipping cost from Japan to Sri Lanka.

    Rough estimate based on vehicle size.
    In production, this would use actual shipping quotes.

    Args:
        vehicle: Vehicle object

    Returns:
        Shipping cost in LKR
    """
    base_shipping = Decimal("150000")  # Base shipping cost

    # Adjust based on engine size (larger vehicles = higher cost)
    if vehicle.engine_cc:
        if vehicle.engine_cc > 2000:
            base_shipping += Decimal("50000")
        elif vehicle.engine_cc > 1500:
            base_shipping += Decimal("30000")

    return base_shipping


# ============================================================================
# CUSTOMS DUTY (Based on engine CC)
# ============================================================================


def calculate_customs_duty(vehicle: Vehicle, vehicle_price_lkr: Decimal) -> Decimal:
    """
    Calculate customs duty based on engine capacity.

    Sri Lanka customs duty rates (2025 - simplified):
    - < 1000cc: 50% of CIF value
    - 1000-1500cc: 75% of CIF value
    - 1500-2000cc: 100% of CIF value
    - 2000-2500cc: 150% of CIF value
    - > 2500cc: 200% of CIF value

    Electric vehicles: 25% (reduced rate)

    Args:
        vehicle: Vehicle object
        vehicle_price_lkr: Vehicle price in LKR

    Returns:
        Customs duty in LKR
    """
    # Electric vehicles get lower rate
    if vehicle.fuel_type == FuelType.ELECTRIC:
        return vehicle_price_lkr * Decimal("0.25")  # 25%

    # Hybrid vehicles get moderate rate
    if vehicle.fuel_type == FuelType.HYBRID:
        return vehicle_price_lkr * Decimal("0.50")  # 50%

    # Based on engine CC
    engine_cc = vehicle.engine_cc or 1500  # Default to 1500 if not specified

    if engine_cc < 1000:
        return vehicle_price_lkr * Decimal("0.50")  # 50%
    elif engine_cc < 1500:
        return vehicle_price_lkr * Decimal("0.75")  # 75%
    elif engine_cc < 2000:
        return vehicle_price_lkr * Decimal("1.00")  # 100%
    elif engine_cc < 2500:
        return vehicle_price_lkr * Decimal("1.50")  # 150%
    else:
        return vehicle_price_lkr * Decimal("2.00")  # 200%


# ============================================================================
# EXCISE DUTY
# ============================================================================


def calculate_excise_duty(vehicle: Vehicle, cif_value: Decimal) -> Decimal:
    """
    Calculate excise duty.

    Excise duty in Sri Lanka (simplified):
    - Typically 20-60% of CIF value depending on vehicle type

    Args:
        vehicle: Vehicle object
        cif_value: CIF value (Cost + Insurance + Freight)

    Returns:
        Excise duty in LKR
    """
    # Electric vehicles: lower excise duty
    if vehicle.fuel_type == FuelType.ELECTRIC:
        return cif_value * Decimal("0.10")  # 10%

    # Hybrid vehicles
    if vehicle.fuel_type == FuelType.HYBRID:
        return cif_value * Decimal("0.25")  # 25%

    # Petrol/Diesel based on engine CC
    engine_cc = vehicle.engine_cc or 1500

    if engine_cc < 1000:
        return cif_value * Decimal("0.20")  # 20%
    elif engine_cc < 1500:
        return cif_value * Decimal("0.30")  # 30%
    elif engine_cc < 2000:
        return cif_value * Decimal("0.40")  # 40%
    else:
        return cif_value * Decimal("0.60")  # 60%


# ============================================================================
# VAT (Value Added Tax)
# ============================================================================


def calculate_vat(taxable_value: Decimal) -> Decimal:
    """
    Calculate VAT (15% in Sri Lanka).

    Args:
        taxable_value: Value subject to VAT

    Returns:
        VAT amount in LKR
    """
    return taxable_value * Decimal("0.15")  # 15% VAT


# ============================================================================
# CESS (Commodity Cess)
# ============================================================================


def calculate_cess(vehicle: Vehicle, cif_value: Decimal) -> Decimal:
    """
    Calculate Cess (commodity tax).

    In Sri Lanka, certain vehicles are subject to cess.
    Simplified: 10% on luxury vehicles (>2500cc)

    Args:
        vehicle: Vehicle object
        cif_value: CIF value

    Returns:
        Cess amount in LKR
    """
    engine_cc = vehicle.engine_cc or 1500

    if engine_cc > 2500:
        return cif_value * Decimal("0.10")  # 10% cess on luxury vehicles

    return Decimal("0")


# ============================================================================
# PORT & SERVICE CHARGES
# ============================================================================


def calculate_port_charges() -> Decimal:
    """
    Calculate port and handling charges.

    Fixed charges for port handling, storage, etc.

    Returns:
        Port charges in LKR
    """
    return Decimal("25000")  # Approximate port charges


def calculate_clearance_fee() -> Decimal:
    """
    Calculate customs clearance agent fee.

    Returns:
        Clearance fee in LKR
    """
    return Decimal("35000")  # Customs clearance service fee


def calculate_documentation_fee() -> Decimal:
    """
    Calculate documentation and processing fees.

    Returns:
        Documentation fee in LKR
    """
    return Decimal("15000")  # Documentation fee


# ============================================================================
# MAIN COST CALCULATOR
# ============================================================================


def calculate_total_cost(
    vehicle: Vehicle, exchange_rate: Decimal = DEFAULT_JPY_TO_LKR
) -> Dict[str, Decimal]:
    """
    Calculate total landed cost for vehicle import.

    Args:
        vehicle: Vehicle object
        exchange_rate: JPY to LKR exchange rate (optional)

    Returns:
        Dictionary with complete cost breakdown
    """
    # Avoid mutating SQLAlchemy model attributes inside calculators.
    price_jpy = Decimal(str(vehicle.price_jpy))
    # Step 1: Convert vehicle price to LKR
    vehicle_price_lkr = price_jpy * exchange_rate

    # Step 2: Calculate shipping
    shipping_cost = calculate_shipping_cost(vehicle)

    # Step 3: CIF Value (Cost + Insurance + Freight)
    cif_value = vehicle_price_lkr + shipping_cost

    # Step 4: Calculate customs duty
    customs_duty = calculate_customs_duty(vehicle, vehicle_price_lkr)

    # Step 5: Calculate excise duty
    excise_duty = calculate_excise_duty(vehicle, cif_value)

    # Step 6: Calculate Cess
    cess = calculate_cess(vehicle, cif_value)

    # Step 7: Taxable value for VAT (CIF + Customs + Excise + Cess)
    taxable_value = cif_value + customs_duty + excise_duty + cess

    # Step 8: Calculate VAT
    vat = calculate_vat(taxable_value)

    # Step 9: Port and service charges
    port_charges = calculate_port_charges()
    clearance_fee = calculate_clearance_fee()
    documentation_fee = calculate_documentation_fee()

    # Step 10: Total cost
    total_cost = (
        vehicle_price_lkr
        + shipping_cost
        + customs_duty
        + excise_duty
        + cess
        + vat
        + port_charges
        + clearance_fee
        + documentation_fee
    )

    # Calculate percentages
    vehicle_percentage = (vehicle_price_lkr / total_cost * Decimal("100")).quantize(Decimal("0.01"))
    taxes_total = customs_duty + excise_duty + cess + vat
    taxes_percentage = (taxes_total / total_cost * Decimal("100")).quantize(Decimal("0.01"))
    fees_total = shipping_cost + port_charges + clearance_fee + documentation_fee
    fees_percentage = (fees_total / total_cost * Decimal("100")).quantize(Decimal("0.01"))

    return {
        "vehicle_price_jpy": price_jpy,
        "vehicle_price_lkr": vehicle_price_lkr.quantize(Decimal("0.01")),
        "exchange_rate": exchange_rate,
        "shipping_cost_lkr": shipping_cost.quantize(Decimal("0.01")),
        "customs_duty_lkr": customs_duty.quantize(Decimal("0.01")),
        "excise_duty_lkr": excise_duty.quantize(Decimal("0.01")),
        "vat_lkr": vat.quantize(Decimal("0.01")),
        "cess_lkr": cess.quantize(Decimal("0.01")),
        "port_charges_lkr": port_charges.quantize(Decimal("0.01")),
        "clearance_fee_lkr": clearance_fee.quantize(Decimal("0.01")),
        "documentation_fee_lkr": documentation_fee.quantize(Decimal("0.01")),
        "total_cost_lkr": total_cost.quantize(Decimal("0.01")),
        "vehicle_percentage": vehicle_percentage,
        "taxes_percentage": taxes_percentage,
        "fees_percentage": fees_percentage,
    }
