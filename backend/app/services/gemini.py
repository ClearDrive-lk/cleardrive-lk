"""
Gemini service for structuring gazette extraction data.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Optional, cast

from app.core.config import settings

logger = logging.getLogger(__name__)

CHAT_SYSTEM_PROMPT = """
You are a helpful vehicle import assistant for ClearDrive.lk.

STRICT RULES YOU MUST FOLLOW:
1. Never ask for, discuss, or mention NIC, KYC, passports, licenses, or personal documents.
2. Never request or process personal or financial information.
3. For tax questions, never calculate taxes yourself. Always say:
   "For accurate tax calculations, please use our Tax Calculator tool."
4. Only recommend vehicles from the provided vehicle list.
5. If no matching vehicles are provided, say so honestly.
6. Keep responses concise, practical, and under 200 words.
"""


class GeminiService:
    """Service for transforming OCR output into tax-rule JSON."""

    def __init__(self) -> None:
        self._model: Any = None

    def _ensure_model(self) -> None:
        if self._model is not None:
            return
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise RuntimeError("google-generativeai is not installed") from exc

        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._model = genai.GenerativeModel(settings.GEMINI_MODEL)

    async def structure_gazette(
        self,
        raw_text: str,
        tables: list[dict[str, Any]],
        gazette_no: str,
    ) -> dict[str, Any]:
        """Structure gazette text/tables into tax-rules JSON."""
        self._ensure_model()
        prompt = f"{self._system_prompt()}\n\n{self._user_prompt(raw_text, tables, gazette_no)}"

        try:
            import google.generativeai as genai

            response = await asyncio.to_thread(
                self._model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )
            data = cast(dict[str, Any], json.loads(response.text))
            self._validate_structure(data)
            return data
        except json.JSONDecodeError as exc:
            raise RuntimeError("Gemini returned invalid JSON") from exc
        except Exception as exc:
            raise RuntimeError(f"Failed to structure gazette data: {exc}") from exc

    def _system_prompt(self) -> str:
        return (
            "You extract Sri Lankan vehicle import tax rules into valid JSON only.\n"
            "Required schema: {gazette_no, effective_date, rules[]}.\n"
            "Each rule: vehicle_type, fuel_type, engine_min, engine_max, customs_percent, "
            "excise_percent, vat_percent, pal_percent, cess_percent, apply_on, notes.\n"
            "Valid apply_on values: CIF, CIF_PLUS_CUSTOMS, CUSTOMS_ONLY, CIF_PLUS_EXCISE."
        )

    def _user_prompt(
        self,
        raw_text: str,
        tables: list[dict[str, Any]],
        gazette_no: str,
    ) -> str:
        tables_text: list[str] = []
        for idx, table in enumerate(tables):
            headers = " | ".join(str(h) for h in table.get("headers", []))
            rows = "\n".join(
                " | ".join(str(v) for v in row.values()) for row in table.get("rows", [])
            )
            tables_text.append(f"Table {idx + 1}\nHeaders: {headers}\n{rows}")

        return (
            f"Gazette number: {gazette_no}\n"
            f"Raw text:\n{raw_text[:6000]}\n\n"
            f"Tables:\n{chr(10).join(tables_text)}"
        )

    def _validate_structure(self, data: dict[str, Any]) -> None:
        for field in ("gazette_no", "effective_date", "rules"):
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        if not isinstance(data["rules"], list):
            raise ValueError("rules must be a list")

        required_rule_fields = {
            "vehicle_type",
            "fuel_type",
            "customs_percent",
            "excise_percent",
            "vat_percent",
        }
        for idx, rule in enumerate(data["rules"]):
            missing = required_rule_fields - set(rule.keys())
            if missing:
                raise ValueError(f"Rule {idx} missing fields: {sorted(missing)}")

    async def chat(
        self,
        user_message: str,
        vehicle_context: list[dict[str, Any]],
        conversation_history: Optional[list[dict[str, str]]] = None,
    ) -> dict[str, Any]:
        """Generate a vehicle-assistant response with hard boundaries."""
        self._ensure_model()

        if self._is_disallowed_user_query(user_message):
            return {
                "message": (
                    "I can only help with vehicle recommendations. "
                    "For accurate tax calculations, please use our Tax Calculator tool."
                ),
                "vehicle_ids": [],
                "contains_boundary_violation": False,
            }

        prompt = self._build_chat_prompt(user_message, vehicle_context, conversation_history or [])

        try:
            import google.generativeai as genai

            response = await asyncio.to_thread(
                self._model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.9,
                    top_k=40,
                    max_output_tokens=500,
                ),
            )
            response_text = str(getattr(response, "text", "") or "").strip()
            if not response_text:
                raise RuntimeError("Gemini returned an empty chat response")
        except Exception as exc:
            raise RuntimeError(f"Gemini chat failed: {exc}") from exc

        violation = self._check_boundaries(response_text)
        if violation is not None:
            response_text = (
                "I apologize, but I can only help with vehicle recommendations. "
                "For tax questions, please use our Tax Calculator tool."
            )

        return {
            "message": response_text,
            "vehicle_ids": self._extract_vehicle_ids(response_text, vehicle_context),
            "contains_boundary_violation": violation is not None,
        }

    def _build_chat_prompt(
        self,
        user_message: str,
        vehicle_context: list[dict[str, Any]],
        conversation_history: list[dict[str, str]],
    ) -> str:
        history_lines = []
        for message in conversation_history[-5:]:
            role = str(message.get("role", "user")).upper()
            content = str(message.get("content", "")).strip()
            if content:
                history_lines.append(f"{role}: {content}")

        vehicles_block = self._format_vehicle_context(vehicle_context)
        history_block = "\n".join(history_lines) or "None"

        return (
            f"{CHAT_SYSTEM_PROMPT}\n\n"
            f"AVAILABLE VEHICLES:\n{vehicles_block}\n\n"
            f"CONVERSATION HISTORY:\n{history_block}\n\n"
            f"USER MESSAGE: {user_message}\n\n"
            "Respond as the ClearDrive vehicle assistant."
        )

    def _format_vehicle_context(self, vehicles: list[dict[str, Any]]) -> str:
        if not vehicles:
            return "No vehicles currently match the query."

        formatted: list[str] = []
        for index, vehicle in enumerate(vehicles, start=1):
            formatted.append(
                f"{index}. {vehicle['make']} {vehicle['model']} ({vehicle['year']}) | "
                f"JPY {vehicle['price_jpy']:,.0f} | {vehicle['vehicle_type'] or 'Unknown type'} | "
                f"{vehicle['fuel_type'] or 'Unknown fuel'} | {vehicle['engine_cc'] or 'N/A'}cc | "
                f"ID: {vehicle['id']}"
            )
        return "\n".join(formatted)

    def _check_boundaries(self, response: str) -> str | None:
        response_lower = response.lower()
        blocked_keywords = [
            ("document_mention", ["nic", "national identity", "identity card", "passport"]),
            (
                "kyc_mention",
                ["kyc", "verification document", "driver's license", "drivers license"],
            ),
            (
                "tax_calculation",
                ["tax is", "duty is", "you'll pay", "you will pay", "total cost is"],
            ),
        ]
        for label, keywords in blocked_keywords:
            if any(keyword in response_lower for keyword in keywords):
                return label
        return None

    def _is_disallowed_user_query(self, user_message: str) -> bool:
        query = user_message.lower()
        blocked_topics = [
            "nic",
            "kyc",
            "passport",
            "license",
            "licence",
            "tax",
            "duty",
            "documents",
        ]
        return any(topic in query for topic in blocked_topics)

    def _extract_vehicle_ids(
        self, response: str, vehicle_context: list[dict[str, Any]]
    ) -> list[str]:
        response_lower = response.lower()
        vehicle_ids: list[str] = []
        for vehicle in vehicle_context:
            make_model = f"{vehicle['make']} {vehicle['model']}".lower()
            if make_model in response_lower:
                vehicle_ids.append(str(vehicle["id"]))
        return vehicle_ids


gemini_service = GeminiService()
