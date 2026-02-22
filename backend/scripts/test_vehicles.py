# backend/scripts/test_vehicles.py

"""
Test vehicle API endpoints.
"""

import requests  # type: ignore

BASE_URL = "http://localhost:8000/api/v1"


def test_vehicle_api():
    """Test vehicle endpoints."""

    print("🧪 Testing Vehicle API\n")

    # Test 1: Get all vehicles
    print("Test 1: Get all vehicles...")
    response = requests.get(f"{BASE_URL}/vehicles", timeout=10)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['total']} vehicles")
        print(f"   Page: {data['page']}/{data['total_pages']}")
        print(f"   First vehicle: {data['vehicles'][0]['make']} {data['vehicles'][0]['model']}\n")
    else:
        print(f"❌ Failed: {response.json()}\n")

    # Test 2: Search vehicles
    print("Test 2: Search for 'Toyota'...")
    response = requests.get(f"{BASE_URL}/vehicles", params={"search": "Toyota"}, timeout=10)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['total']} Toyota vehicles\n")
    else:
        print(f"❌ Failed: {response.json()}\n")

    # Test 3: Filter by price range
    print("Test 3: Filter by price (1,000,000 - 1,500,000 JPY)...")
    response = requests.get(
        f"{BASE_URL}/vehicles",
        params={
            "price_min": 1000000,
            "price_max": 1500000,
            "sort_by": "price_jpy",
            "sort_order": "asc",
        },
        timeout=10,
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['total']} vehicles in price range")
        if data["vehicles"]:
            for v in data["vehicles"][:3]:
                print(
                    f"   - {v['make']} {v['model']} ({v['year']}) - ¥{int(float(v['price_jpy'])):,}"
                )

        print()
    else:
        print(f"❌ Failed: {response.json()}\n")

    # Test 4: Filter by fuel type
    print("Test 4: Filter by fuel type (HYBRID)...")
    response = requests.get(f"{BASE_URL}/vehicles", params={"fuel_type": "HYBRID"}, timeout=10)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['total']} hybrid vehicles\n")
    else:
        print(f"❌ Failed: {response.json()}\n")

    # Test 5: Get specific vehicle
    print("Test 5: Get specific vehicle details...")

    # First, get a vehicle ID
    response = requests.get(f"{BASE_URL}/vehicles", params={"limit": 1}, timeout=10)
    if response.status_code == 200:
        vehicle_id = response.json()["vehicles"][0]["id"]

        # Now get that vehicle
        response = requests.get(f"{BASE_URL}/vehicles/{vehicle_id}", timeout=10)

        if response.status_code == 200:
            vehicle = response.json()
            print("✅ Retrieved vehicle:")
            print(f"   Make/Model: {vehicle['make']} {vehicle['model']}")
            print(f"   Year: {vehicle['year']}")
            print(f"   Price: ¥{float(vehicle['price_jpy']):,.0f}")
            print(f"   Mileage: {vehicle['mileage_km']:,} km")
            print(f"   Fuel: {vehicle['fuel_type']}")
            print(f"   Transmission: {vehicle['transmission']}\n")

            # Test 6: Calculate cost for this vehicle
            print("Test 6: Calculate import cost...")
            response = requests.get(f"{BASE_URL}/vehicles/{vehicle_id}/cost", timeout=10)

            if response.status_code == 200:
                cost = response.json()
                print("✅ Cost breakdown:")
                print(f"   Vehicle Price (JPY): ¥{float(cost['vehicle_price_jpy']):,.0f}")
                print(f"   Vehicle Price (LKR): Rs. {float(cost['vehicle_price_lkr']):,.2f}")
                print(f"   Exchange Rate: {cost['exchange_rate']}")
                print(f"   Shipping Cost: Rs. {float(cost['shipping_cost_lkr']):,.2f}")
                print(f"   Customs Duty: Rs. {float(cost['customs_duty_lkr']):,.2f}")
                print(f"   Excise Duty: Rs. {float(cost['excise_duty_lkr']):,.2f}")
                print(f"   VAT (15%): Rs. {float(cost['vat_lkr']):,.2f}")
                print(f"   Port Charges: Rs. {float(cost['port_charges_lkr']):,.2f}")
                print(f"   Clearance Fee: Rs. {float(cost['clearance_fee_lkr']):,.2f}")
                print(f"   Documentation: Rs. {float(cost['documentation_fee_lkr']):,.2f}")
                print("   ─────────────────────────────────────")
                print(f"   TOTAL COST: Rs. {float(cost['total_cost_lkr']):,.2f}")
                print("\n   Breakdown:")
                print(f"   - Vehicle: {cost['vehicle_percentage']:.1f}%")
                print(f"   - Taxes: {cost['taxes_percentage']:.1f}%")
                print(f"   - Fees: {cost['fees_percentage']:.1f}%\n")
            else:
                print(f"❌ Cost calculation failed: {response.json()}\n")
        else:
            print(f"❌ Failed to get vehicle: {response.json()}\n")

    # Test 7: Filter combinations
    print("Test 7: Complex filters (Hybrid, <1500cc, under ¥1,500,000)...")
    response = requests.get(
        f"{BASE_URL}/vehicles",
        params={
            "fuel_type": "HYBRID",
            "price_max": 1500000,
            "sort_by": "price_jpy",
            "sort_order": "asc",
        },
        timeout=10,
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['total']} matching vehicles")
        if data["vehicles"]:
            for v in data["vehicles"]:
                print(
                    f"   - {v['make']} {v['model']} - "
                    f"¥{float(v['price_jpy']):,.0f} ({v['engine_cc']}cc)"
                )
        print()
    else:
        print(f"❌ Failed: {response.json()}\n")

    print("✅ All vehicle API tests completed!")


if __name__ == "__main__":
    test_vehicle_api()
