from __future__ import annotations

import logging
import re
from decimal import Decimal
from typing import Literal

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.rate_limit import rate_limit
from app.modules.auth.models import User
from app.modules.vehicles.models import Vehicle, VehicleStatus
from app.services.gemini import gemini_service
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import case, or_
from sqlalchemy.orm import Session

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=settings.CHATBOT_MAX_MESSAGE_LENGTH)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=settings.CHATBOT_MAX_MESSAGE_LENGTH)
    conversation_history: list[ConversationMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    message: str
    vehicle_ids: list[str]
    suggested_action: str | None = None


def _extract_price_cap(text: str) -> Decimal | None:
    lowered = text.lower()
    patterns = [
        r"(?:under|below|max)\s*\$?\s*([\d,]+)\s*k\b",
        r"(?:under|below|max)\s*\$?\s*([\d,]+)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, lowered)
        if match is None:
            continue
        amount = Decimal(match.group(1).replace(",", ""))
        if "k" in match.group(0):
            amount *= Decimal("1000")
        return amount
    return None


def _normalized_terms(text: str) -> set[str]:
    return {term for term in re.findall(r"[a-z0-9]+", text.lower()) if len(term) > 1}


def search_vehicles(db: Session, query_text: str) -> list[dict[str, object]]:
    terms = _normalized_terms(query_text)
    query = db.query(Vehicle).filter(Vehicle.status == VehicleStatus.AVAILABLE)

    price_cap = _extract_price_cap(query_text)
    if price_cap is not None:
        query = query.filter(Vehicle.price_jpy <= price_cap)

    vehicle_type_filters = {
        "suv": "SUV",
        "sedan": "Sedan",
        "hatchback": "Hatchback",
        "wagon": "Wagon",
        "van": "Van/minivan",
        "pickup": "Pickup",
    }
    for term, vehicle_type in vehicle_type_filters.items():
        if term in terms:
            query = query.filter(Vehicle.vehicle_type == vehicle_type)
            break

    fuel_filters = {
        "hybrid": "hybrid",
        "electric": "electric",
        "diesel": "diesel",
        "petrol": "gasoline",
        "gasoline": "gasoline",
    }
    for term, fuel_text in fuel_filters.items():
        if term in terms:
            query = query.filter(Vehicle.fuel_type.ilike(f"%{fuel_text}%"))
            break

    text_score = case(
        *[
            (
                or_(
                    Vehicle.make.ilike(f"%{term}%"),
                    Vehicle.model.ilike(f"%{term}%"),
                    Vehicle.grade.ilike(f"%{term}%"),
                    Vehicle.body_type.ilike(f"%{term}%"),
                    Vehicle.options.ilike(f"%{term}%"),
                    Vehicle.other_remarks.ilike(f"%{term}%"),
                ),
                1,
            )
            for term in terms
        ],
        else_=0,
    )

    vehicles = query.order_by(text_score.desc(), Vehicle.created_at.desc()).limit(5).all()

    return [
        {
            "id": str(vehicle.id),
            "make": vehicle.make,
            "model": vehicle.model,
            "year": vehicle.year,
            "price_jpy": float(vehicle.price_jpy),
            "vehicle_type": (
                vehicle.vehicle_type.value
                if getattr(vehicle.vehicle_type, "value", None) is not None
                else vehicle.vehicle_type
            ),
            "fuel_type": vehicle.fuel_type,
            "engine_cc": vehicle.engine_cc,
            "image_url": vehicle.image_url,
        }
        for vehicle in vehicles
    ]


def _fallback_chat_response(vehicle_context: list[dict[str, object]]) -> dict[str, object]:
    if not vehicle_context:
        return {
            "message": (
                "I could not find a strong vehicle match yet.\n"
                "Try adding two details so I can narrow it faster:\n"
                "- Budget range (for example: under JPY 2,000,000)\n"
                "- Body or fuel preference (SUV, sedan, hybrid, electric)\n"
                "Would you like city-focused options or family-focused options?"
            ),
            "vehicle_ids": [],
            "suggested_action": None,
        }

    shortlisted = vehicle_context[:3]
    lines = []
    for vehicle in shortlisted:
        price_value = vehicle.get("price_jpy")
        price = "N/A"
        if isinstance(price_value, (int, float)):
            price = f"JPY {price_value:,.0f}"
        vehicle_type = str(vehicle.get("vehicle_type") or "vehicle")
        fuel = str(vehicle.get("fuel_type") or "unknown fuel")
        lines.append(
            f"- {vehicle['make']} {vehicle['model']} ({vehicle['year']}) - {price}: "
            f"{vehicle_type}, {fuel}"
        )

    return {
        "message": (
            "Here are a few vehicles that fit your request:\n"
            f"{chr(10).join(lines)}\n"
            "Open any vehicle card to compare more details. "
            "Do you want me to narrow this to lower running cost, newer year, or more cabin space?"
        ),
        "vehicle_ids": [str(vehicle["id"]) for vehicle in shortlisted],
        "suggested_action": None,
    }


@router.post("/message", response_model=ChatResponse)
@rate_limit("chat")
async def chat_message(
    payload: ChatRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if len(payload.conversation_history) > settings.CHATBOT_MAX_HISTORY_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Conversation history too long "
                f"(max {settings.CHATBOT_MAX_HISTORY_LENGTH} messages)"
            ),
        )

    vehicle_context = search_vehicles(db, payload.message)
    try:
        ai_response = await gemini_service.chat(
            user_message=payload.message,
            vehicle_context=vehicle_context,
            conversation_history=[
                {"role": message.role, "content": message.content}
                for message in payload.conversation_history
            ],
        )
    except Exception as exc:
        logger.exception("Gemini chat failed, using local fallback: %s", exc)
        ai_response = _fallback_chat_response(vehicle_context)

    suggested_action = None
    if "tax calculator" in str(ai_response["message"]).lower():
        suggested_action = "open_tax_calculator"

    logger.info(
        "Chat response generated for user_id=%s with %s linked vehicles",
        current_user.id,
        len(ai_response["vehicle_ids"]),
    )
    return ChatResponse(
        message=str(ai_response["message"]),
        vehicle_ids=[str(vehicle_id) for vehicle_id in ai_response["vehicle_ids"]],
        suggested_action=suggested_action,
    )
