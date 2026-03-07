"""
Mock vehicle scraper for CD-23 development/testing.
"""

from __future__ import annotations

import copy
import random
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


class MockVehicleScraper:
    """
    Deterministic mock scraper.

    It always emits the same base inventory so duplicate prevention can be
    verified across repeated runs. A small subset can be mutated to simulate
    meaningful updates.
    """

    _BASE_VEHICLES: list[dict[str, Any]] = [
        {
            "stock_no": "CD23-001",
            "chassis": "TOY2024-100001",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2024,
            "reg_year": "2024/5",
            "vehicle_type": "Sedan",
            "body_type": "Sedan",
            "grade": "G",
            "price_jpy": 2450000,
            "mileage_km": 28000,
            "engine_cc": 1800,
            "fuel_type": "Gasoline",
            "transmission": "Automatic",
            "drive": "2WD",
            "seats": 5,
            "doors": 4,
            "color": "White",
            "location": "Japan > Yokohama",
            "status": "AVAILABLE",
            "image_url": "https://example.com/mock/cd23-001.jpg",
            "vehicle_url": "https://example.com/mock/cd23-001",
            "options": "Navigation, Reverse Camera, Smart Key",
            "other_remarks": "Well maintained sedan.",
        },
        {
            "stock_no": "CD23-002",
            "chassis": "HON2023-100002",
            "make": "Honda",
            "model": "Vezel",
            "year": 2023,
            "reg_year": "2023/8",
            "vehicle_type": "SUV",
            "body_type": "SUV",
            "grade": "Hybrid Z",
            "price_jpy": 3290000,
            "mileage_km": 36000,
            "engine_cc": 1500,
            "fuel_type": "Gasoline/hybrid",
            "transmission": "Automatic",
            "drive": "2WD",
            "seats": 5,
            "doors": 5,
            "color": "Pearl",
            "location": "Japan > Nagoya",
            "status": "AVAILABLE",
            "image_url": "https://example.com/mock/cd23-002.jpg",
            "vehicle_url": "https://example.com/mock/cd23-002",
            "options": "Cruise Control, LED Lights, Bluetooth",
            "other_remarks": "Comfortable family SUV.",
        },
        {
            "stock_no": "CD23-003",
            "chassis": "NIS2025-100003",
            "make": "Nissan",
            "model": "Note",
            "year": 2025,
            "reg_year": "2025/2",
            "vehicle_type": "Hatchback",
            "body_type": "Hatchback",
            "grade": "X",
            "price_jpy": 1980000,
            "mileage_km": 12000,
            "engine_cc": 1200,
            "fuel_type": "Gasoline",
            "transmission": "CVT",
            "drive": "2WD",
            "seats": 5,
            "doors": 5,
            "color": "Silver",
            "location": "Japan > Osaka",
            "status": "AVAILABLE",
            "image_url": "https://example.com/mock/cd23-003.jpg",
            "vehicle_url": "https://example.com/mock/cd23-003",
            "options": "Auto AC, Reverse Camera",
            "other_remarks": "Low mileage urban hatchback.",
        },
        {
            "stock_no": "CD23-004",
            "chassis": "MAZ2024-100004",
            "make": "Mazda",
            "model": "CX-5",
            "year": 2024,
            "reg_year": "2024/9",
            "vehicle_type": "SUV",
            "body_type": "SUV",
            "grade": "20S",
            "price_jpy": 3580000,
            "mileage_km": 19000,
            "engine_cc": 2000,
            "fuel_type": "Gasoline",
            "transmission": "Automatic",
            "drive": "AWD",
            "seats": 5,
            "doors": 5,
            "color": "Gray",
            "location": "Japan > Tokyo",
            "status": "AVAILABLE",
            "image_url": "https://example.com/mock/cd23-004.jpg",
            "vehicle_url": "https://example.com/mock/cd23-004",
            "options": "Leather Seats, Cruise Control",
            "other_remarks": "Premium compact SUV.",
        },
        {
            "stock_no": "CD23-005",
            "chassis": "SUZ2023-100005",
            "make": "Suzuki",
            "model": "Swift",
            "year": 2023,
            "reg_year": "2023/11",
            "vehicle_type": "Hatchback",
            "body_type": "Hatchback",
            "grade": "RS",
            "price_jpy": 1680000,
            "mileage_km": 41000,
            "engine_cc": 1200,
            "fuel_type": "Gasoline",
            "transmission": "Automatic",
            "drive": "2WD",
            "seats": 5,
            "doors": 5,
            "color": "Red",
            "location": "Japan > Kobe",
            "status": "AVAILABLE",
            "image_url": "https://example.com/mock/cd23-005.jpg",
            "vehicle_url": "https://example.com/mock/cd23-005",
            "options": "Smart Key, Bluetooth",
            "other_remarks": "Reliable and fuel efficient.",
        },
        {
            "stock_no": "CD23-006",
            "chassis": "MIT2025-100006",
            "make": "Mitsubishi",
            "model": "Outlander",
            "year": 2025,
            "reg_year": "2025/1",
            "vehicle_type": "SUV",
            "body_type": "SUV",
            "grade": "PHEV",
            "price_jpy": 4390000,
            "mileage_km": 9000,
            "engine_cc": 2400,
            "fuel_type": "Plugin Hybrid",
            "transmission": "Automatic",
            "drive": "4WD",
            "seats": 7,
            "doors": 5,
            "color": "Black",
            "location": "Japan > Yokohama",
            "status": "AVAILABLE",
            "image_url": "https://example.com/mock/cd23-006.jpg",
            "vehicle_url": "https://example.com/mock/cd23-006",
            "options": "Navigation, Sunroof, Heated Seats",
            "other_remarks": "Plug-in hybrid 7-seater.",
        },
    ]

    def __init__(self, update_probability: float = 0.2) -> None:
        self.update_probability = update_probability

    def scrape(self, count: int = 10) -> list[dict[str, Any]]:
        vehicles: list[dict[str, Any]] = []
        pool = copy.deepcopy(self._BASE_VEHICLES)

        for idx in range(min(count, len(pool))):
            vehicle = pool[idx]
            vehicle["scraped_at"] = datetime.now(UTC).isoformat()
            vehicle["source"] = "MOCK_SCRAPER"

            if random.random() < self.update_probability:
                self._apply_random_change(vehicle)

            vehicles.append(vehicle)

        return vehicles

    def _apply_random_change(self, vehicle: dict[str, Any]) -> None:
        mutation = random.choice(["price", "mileage", "status", "image"])
        if mutation == "price":
            baseline = Decimal(str(vehicle["price_jpy"]))
            delta = Decimal("0.06") if random.random() < 0.5 else Decimal("0.08")
            direction = Decimal("-1") if random.random() < 0.5 else Decimal("1")
            vehicle["price_jpy"] = int(
                (baseline + (baseline * delta * direction)).quantize(Decimal("1"))
            )
        elif mutation == "mileage":
            vehicle["mileage_km"] = int(vehicle.get("mileage_km", 0)) + random.randint(1200, 3500)
        elif mutation == "status":
            vehicle["status"] = random.choice(["AVAILABLE", "RESERVED", "SOLD"])
        else:
            vehicle["image_url"] = f"{vehicle.get('image_url')}?v=2"
