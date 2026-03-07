"""
Gemini service for structuring gazette extraction data.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


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
        self._model = genai.GenerativeModel("gemini-1.5-pro")

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
            data = json.loads(response.text)
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


gemini_service = GeminiService()
