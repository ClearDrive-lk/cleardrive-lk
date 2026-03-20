"""
Gemini service for structuring gazette extraction data.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
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
        self._active_model_name: str | None = None

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
        self._active_model_name = settings.GEMINI_MODEL

    async def structure_gazette(
        self,
        raw_text: str,
        tables: list[dict[str, Any]],
        gazette_no: str,
    ) -> dict[str, Any]:
        """Structure gazette text/tables into tax-rules JSON."""
        self._ensure_model()

        try:
            import google.generativeai as genai

            chunks = self._build_structuring_chunks(raw_text, tables)
            merged_rules: list[dict[str, Any]] = []
            merged: dict[str, Any] = {
                "gazette_no": gazette_no,
                "effective_date": None,
                "rules": merged_rules,
            }
            seen_rule_keys: set[tuple[str, ...]] = set()

            for chunk_index, (chunk_text, chunk_tables) in enumerate(chunks, start=1):
                data = await self._structure_chunk(
                    raw_text=chunk_text,
                    tables=chunk_tables,
                    gazette_no=gazette_no,
                    chunk_index=chunk_index,
                    chunk_count=len(chunks),
                    genai=genai,
                )
                if not merged["effective_date"] and data.get("effective_date"):
                    merged["effective_date"] = data["effective_date"]
                for rule in cast(list[dict[str, Any]], data.get("rules", [])):
                    key = self._rule_identity(rule)
                    if key in seen_rule_keys:
                        continue
                    seen_rule_keys.add(key)
                    merged_rules.append(rule)

            self._validate_structure(cast(dict[str, Any], merged))
            return cast(dict[str, Any], merged)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Gemini returned invalid JSON") from exc
        except Exception as exc:
            raise RuntimeError(f"Failed to structure gazette data: {exc}") from exc

    async def _structure_chunk(
        self,
        *,
        raw_text: str,
        tables: list[dict[str, Any]],
        gazette_no: str,
        chunk_index: int,
        chunk_count: int,
        genai: Any,
    ) -> dict[str, Any]:
        prompts = [
            self._build_structuring_prompt(
                raw_text,
                tables,
                gazette_no,
                text_limit=6000,
                chunk_index=chunk_index,
                chunk_count=chunk_count,
            ),
            self._build_structuring_prompt(
                raw_text,
                tables[:3],
                gazette_no,
                text_limit=3000,
                chunk_index=chunk_index,
                chunk_count=chunk_count,
            ),
            self._build_structuring_prompt(
                raw_text,
                [],
                gazette_no,
                text_limit=1500,
                chunk_index=chunk_index,
                chunk_count=chunk_count,
            ),
        ]
        last_error: Exception | None = None
        for prompt in prompts:
            try:
                response = await self._generate_structured_content(prompt, genai)
                response_text = str(getattr(response, "text", "") or "").strip()
                data = cast(dict[str, Any], json.loads(self._extract_json_payload(response_text)))
                self._validate_structure(data)
                return data
            except Exception as exc:
                last_error = exc
                if "deadline exceeded" not in str(exc).lower():
                    raise
                logger.warning(
                    "Gemini structuring timed out for chunk %s/%s; retrying with a smaller prompt",
                    chunk_index,
                    chunk_count,
                )

        assert last_error is not None
        raise last_error

    async def _generate_structured_content(self, prompt: str, genai: Any) -> Any:
        assert self._model is not None
        try:
            return await asyncio.to_thread(
                self._model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                ),
            )
        except Exception as exc:
            message = str(exc)
            if "is not found for api version" not in message.lower():
                raise

            fallback_models = [
                "gemini-2.5-flash",
                "gemini-flash-latest",
                "gemini-2.5-flash-lite",
            ]
            tried = {self._active_model_name or settings.GEMINI_MODEL}
            last_error: Exception = exc
            for model_name in fallback_models:
                if model_name in tried:
                    continue
                try:
                    self._model = genai.GenerativeModel(model_name)
                    self._active_model_name = model_name
                    logger.warning("Falling back to Gemini model %s", model_name)
                    return await asyncio.to_thread(
                        self._model.generate_content,
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.1,
                        ),
                    )
                except Exception as fallback_exc:
                    tried.add(model_name)
                    last_error = fallback_exc
                    continue
            raise last_error

    def _system_prompt(self) -> str:
        return (
            "You extract Sri Lankan vehicle import tax rules into valid JSON only.\n"
            "Do not wrap the response in markdown fences or explanations.\n"
            "Required schema: {gazette_no, effective_date, rules[]}.\n"
            "Each rule must include rule_type and use one of: VEHICLE_TAX, CUSTOMS, SURCHARGE, LUXURY.\n"
            "VEHICLE_TAX fields: vehicle_type, fuel_type, category_code, hs_code, engine_min, engine_max, "
            "power_kw_min, power_kw_max, age_years_min, age_years_max, excise_type, excise_rate, "
            "excise_percent, excise_per_kw_amount, notes.\n"
            "CUSTOMS fields: hs_code, customs_percent, vat_percent, pal_percent, cess_type, cess_value, notes.\n"
            "SURCHARGE fields: name, rate_percent, applies_to, notes.\n"
            "LUXURY fields: hs_code, threshold_value, rate_percent, notes.\n"
            "vehicle_type must be one of: SEDAN, SUV, TRUCK, VAN, MOTORCYCLE, ELECTRIC, BUS, OTHER.\n"
            "fuel_type must be one of: PETROL, DIESEL, ELECTRIC, HYBRID, OTHER.\n"
            "Use category_code for more specific labels such as PASSENGER_VEHICLE_BEV or "
            "GOODS_VEHICLE_ELECTRIC.\n"
            "If a rule is specific to a motor-power band, store that in power_kw_min/power_kw_max.\n"
            "If a rule is specific to vehicle age, store that in age_years_min/age_years_max.\n"
            "If a rule says Rs. X per kW, store X in excise_per_kw_amount and do not bury it in notes.\n"
            "Every VEHICLE_TAX rule must include hs_code, power range, and age range.\n"
            "Extract every rule visible in the provided chunk. Do not stop after the first section.\n"
            "If a PDF provides only some components, emit the matching rule_type only.\n"
            "Valid apply_on values: CIF, CIF_PLUS_CUSTOMS, CUSTOMS_ONLY, CIF_PLUS_EXCISE."
        )

    def _user_prompt(
        self,
        raw_text: str,
        tables: list[dict[str, Any]],
        gazette_no: str,
        *,
        text_limit: int = 6000,
        chunk_index: int = 1,
        chunk_count: int = 1,
    ) -> str:
        hs_codes = self._extract_hs_codes(raw_text)
        tables_text: list[str] = []
        for idx, table in enumerate(tables):
            headers = " | ".join(str(h) for h in table.get("headers", []))
            rows = "\n".join(
                " | ".join(str(v) for v in row.values()) for row in table.get("rows", [])
            )
            tables_text.append(f"Table {idx + 1}\nHeaders: {headers}\n{rows}")

        return (
            f"Gazette number: {gazette_no}\n"
            f"Chunk: {chunk_index} of {chunk_count}\n"
            f"HS codes seen in this chunk: {', '.join(hs_codes) if hs_codes else 'None detected'}\n"
            f"Raw text:\n{raw_text[:text_limit]}\n\n"
            f"Tables:\n{chr(10).join(tables_text)}"
        )

    def _build_structuring_prompt(
        self,
        raw_text: str,
        tables: list[dict[str, Any]],
        gazette_no: str,
        *,
        text_limit: int,
        chunk_index: int,
        chunk_count: int,
    ) -> str:
        return (
            f"{self._system_prompt()}\n\n"
            f"{self._user_prompt(raw_text, tables, gazette_no, text_limit=text_limit, chunk_index=chunk_index, chunk_count=chunk_count)}"
        )

    def _build_structuring_chunks(
        self, raw_text: str, tables: list[dict[str, Any]]
    ) -> list[tuple[str, list[dict[str, Any]]]]:
        normalized_text = raw_text.strip()
        if len(normalized_text) <= 6000 and len(tables) <= 3:
            return [(normalized_text, tables)]

        target_len = 4500
        hs_matches = list(re.finditer(r"\b\d{4}\.\d{2}\.\d{2}\b", normalized_text))
        chunks: list[str] = []

        if hs_matches:
            sections: list[str] = []
            for index, match in enumerate(hs_matches):
                start = match.start()
                end = (
                    hs_matches[index + 1].start()
                    if index + 1 < len(hs_matches)
                    else len(normalized_text)
                )
                section = normalized_text[start:end].strip()
                if section:
                    sections.append(section)

            current_sections: list[str] = []
            current_len = 0
            for section in sections:
                section_len = len(section) + 1
                if current_sections and current_len >= target_len:
                    chunks.append("\n".join(current_sections))
                    current_sections = []
                    current_len = 0
                current_sections.append(section)
                current_len += section_len
            if current_sections:
                chunks.append("\n".join(current_sections))
        else:
            start = 0
            step = 4000
            overlap = 500
            while start < len(normalized_text):
                end = min(len(normalized_text), start + step)
                chunk = normalized_text[start:end].strip()
                if chunk:
                    chunks.append(chunk)
                if end >= len(normalized_text):
                    break
                start = max(end - overlap, start + 1)

        if not chunks:
            chunks = [normalized_text[:6000]]

        return [(chunk, []) for chunk in chunks]

    def _extract_hs_codes(self, text: str) -> list[str]:
        seen: list[str] = []
        for match in re.findall(r"\b\d{4}\.\d{2}\.\d{2}\b", text):
            if match not in seen:
                seen.append(match)
        return seen

    def _rule_identity(self, rule: dict[str, Any]) -> tuple[str, ...]:
        return tuple(
            str(rule.get(field) if rule.get(field) is not None else "")
            for field in (
                "vehicle_type",
                "fuel_type",
                "category_code",
                "hs_code",
                "engine_min",
                "engine_max",
                "power_kw_min",
                "power_kw_max",
                "age_years_min",
                "age_years_max",
                "excise_type",
                "excise_rate",
                "customs_percent",
                "excise_percent",
                "excise_per_kw_amount",
                "vat_percent",
                "pal_percent",
                "cess_percent",
                "cess_type",
                "cess_value",
                "threshold_value",
                "rate_percent",
                "applies_to",
                "name",
                "apply_on",
                "notes",
            )
        )

    def _extract_json_payload(self, response_text: str) -> str:
        if not response_text:
            raise RuntimeError("Gemini returned an empty response")

        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`").strip()
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise RuntimeError("Gemini response did not contain a JSON object")
        return cleaned[start : end + 1]

    def _validate_structure(self, data: dict[str, Any]) -> None:
        for field in ("gazette_no", "effective_date", "rules"):
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        if not isinstance(data["rules"], list):
            raise ValueError("rules must be a list")

        for idx, rule in enumerate(data["rules"]):
            if "rule_type" not in rule:
                if "vehicle_type" in rule and "fuel_type" in rule:
                    rule["rule_type"] = "VEHICLE_TAX"
                else:
                    raise ValueError(f"Rule {idx} missing fields: ['rule_type']")

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
