from __future__ import annotations

from decimal import Decimal

from app.modules.vehicles.models import FuelType, Vehicle, VehicleStatus, VehicleType


def _create_vehicle(db, stock_no: str, **overrides) -> Vehicle:
    payload = {
        "stock_no": stock_no,
        "make": "Toyota",
        "model": "RAV4",
        "year": 2020,
        "price_jpy": Decimal("18000"),
        "vehicle_type": VehicleType.SUV,
        "fuel_type": FuelType.HYBRID.value,
        "engine_cc": 2000,
        "status": VehicleStatus.AVAILABLE,
    }
    payload.update(overrides)
    vehicle = Vehicle(**payload)
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


def test_chat_message_returns_ai_response_with_vehicle_ids(
    client, db, auth_headers, test_user, monkeypatch
):
    vehicle = _create_vehicle(db, "CHAT-001")

    async def _chat(user_message, vehicle_context, conversation_history):
        assert user_message == "I need a family SUV"
        assert str(vehicle.id) in [item["id"] for item in vehicle_context]
        return {
            "message": "The Toyota RAV4 looks like a strong family SUV option.",
            "vehicle_ids": [str(vehicle.id)],
            "contains_boundary_violation": False,
        }

    monkeypatch.setattr("app.modules.chat.routes.gemini_service.chat", _chat)

    response = client.post(
        "/api/v1/chat/message",
        headers=auth_headers,
        json={"message": "I need a family SUV", "conversation_history": []},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["vehicle_ids"] == [str(vehicle.id)]
    assert payload["suggested_action"] is None


def test_chat_message_injects_top_five_vehicle_results(client, db, auth_headers, monkeypatch):
    vehicles = [
        _create_vehicle(db, f"CHAT-{index:03d}", model=f"Model {index}") for index in range(1, 7)
    ]
    captured_context: dict[str, object] = {}

    async def _chat(user_message, vehicle_context, conversation_history):
        captured_context["count"] = len(vehicle_context)
        captured_context["ids"] = [item["id"] for item in vehicle_context]
        return {
            "message": "Top options are available.",
            "vehicle_ids": [item["id"] for item in vehicle_context[:2]],
            "contains_boundary_violation": False,
        }

    monkeypatch.setattr("app.modules.chat.routes.gemini_service.chat", _chat)

    response = client.post(
        "/api/v1/chat/message",
        headers=auth_headers,
        json={"message": "Show me SUVs", "conversation_history": []},
    )

    assert response.status_code == 200
    assert captured_context["count"] == 5
    assert set(captured_context["ids"]).issubset({str(vehicle.id) for vehicle in vehicles})


def test_chat_message_sets_tax_calculator_action(client, auth_headers, monkeypatch):
    async def _chat(user_message, vehicle_context, conversation_history):
        return {
            "message": "For accurate tax calculations, please use our Tax Calculator tool.",
            "vehicle_ids": [],
            "contains_boundary_violation": False,
        }

    monkeypatch.setattr("app.modules.chat.routes.gemini_service.chat", _chat)

    response = client.post(
        "/api/v1/chat/message",
        headers=auth_headers,
        json={"message": "What tax will I pay?", "conversation_history": []},
    )

    assert response.status_code == 200
    assert response.json()["suggested_action"] == "open_tax_calculator"


def test_chat_message_rate_limits_after_ten_requests(client, auth_headers, monkeypatch):
    async def _chat(user_message, vehicle_context, conversation_history):
        return {
            "message": "Here are a few vehicles to consider.",
            "vehicle_ids": [],
            "contains_boundary_violation": False,
        }

    store: dict[str, int] = {}

    class FakeRedis:
        async def incr(self, key: str) -> int:
            value = store.get(key, 0) + 1
            store[key] = value
            return value

        async def expire(self, key: str, _window: int) -> bool:
            return True

    async def _get_redis():
        return FakeRedis()

    monkeypatch.setattr("app.modules.chat.routes.gemini_service.chat", _chat)
    monkeypatch.setattr("app.core.rate_limit.get_redis", _get_redis)

    for _ in range(10):
        response = client.post(
            "/api/v1/chat/message",
            headers=auth_headers,
            json={"message": "Recommend a vehicle", "conversation_history": []},
        )
        assert response.status_code == 200

    limited = client.post(
        "/api/v1/chat/message",
        headers=auth_headers,
        json={"message": "Recommend a vehicle", "conversation_history": []},
    )

    assert limited.status_code == 429
    assert limited.json()["detail"]["error"] == "Rate limit exceeded"
