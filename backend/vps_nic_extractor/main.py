"""
CD-51 VPS NIC extraction service.

Privacy rules:
- Process images in memory only.
- Never write uploaded images to disk.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
from io import BytesIO
from typing import Any, cast

import httpx
from fastapi import FastAPI, File, Header, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field, ValidationError
from PIL import Image

logger = logging.getLogger("nic_extractor")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")

INTERNAL_SECRET = os.getenv("INTERNAL_SECRET", "")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "minicpm-v:latest")

ALLOWED_MIME_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


class FrontSchema(BaseModel):
    nic_number: str = Field(min_length=8, max_length=32)
    full_name: str = Field(min_length=1, max_length=255)
    date_of_birth: str = Field(min_length=4, max_length=32)


class BackSchema(BaseModel):
    address: str = Field(min_length=1, max_length=500)
    gender: str = Field(min_length=1, max_length=16)
    issue_date: str = Field(min_length=4, max_length=32)


app = FastAPI(title="ClearDrive NIC Extractor", version="1.0.0")


@app.get("/")
async def root():
    return {
        "service": "NIC Extraction",
        "mode": "vps",
        "model": OLLAMA_MODEL,
    }


@app.middleware("http")
async def request_log_middleware(request: Request, call_next):
    # Intentionally log metadata only.
    client_host = request.client.host if request.client is not None else "-"
    logger.info("request %s %s from=%s", request.method, request.url.path, client_host)
    response = await call_next(request)
    logger.info("response %s %s", request.url.path, response.status_code)
    return response


def _verify_secret(secret: str | None) -> None:
    if not INTERNAL_SECRET:
        raise HTTPException(status_code=500, detail="INTERNAL_SECRET not configured")
    if secret != INTERNAL_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")


def _extract_json(text: str) -> dict[str, Any]:
    # Extract first JSON object in model output.
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model response")
    return cast(dict[str, Any], json.loads(match.group(0)))


def _prompt_for(side: str) -> str:
    if side == "front":
        return (
            "Extract Sri Lankan NIC FRONT fields and return ONLY JSON with keys: "
            "nic_number, full_name, date_of_birth. "
            "If missing, return empty string values."
        )
    return (
        "Extract Sri Lankan NIC BACK fields and return ONLY JSON with keys: "
        "address, gender, issue_date. "
        "If missing, return empty string values."
    )


async def _extract_with_ollama(image_bytes: bytes, side: str) -> dict[str, Any]:
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": _prompt_for(side),
        "images": [image_b64],
        "stream": False,
        "options": {"temperature": 0.1, "top_p": 0.9},
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
    if response.status_code != 200:
        raise RuntimeError(f"Ollama error {response.status_code}: {response.text[:500]}")
    body = response.json()
    raw_text = str(body.get("response", ""))
    parsed = _extract_json(raw_text)

    try:
        validated: FrontSchema | BackSchema
        if side == "front":
            validated = FrontSchema.model_validate(parsed)
        else:
            validated = BackSchema.model_validate(parsed)
    except ValidationError as exc:
        raise RuntimeError(f"Schema validation failed: {exc}") from exc

    payload = validated.model_dump()
    payload.update({"confidence": 0.85, "side": side})
    return payload


@app.get("/health")
async def health(x_internal_secret: str | None = Header(default=None, alias="X-Internal-Secret")):
    _verify_secret(x_internal_secret)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
        if response.status_code != 200:
            return {"status": "degraded", "ollama": "error", "code": response.status_code}
        models = response.json().get("models", [])
        has_minicpm = any("minicpm-v" in str(m.get("name", "")) for m in models)
        return {
            "status": "healthy" if has_minicpm else "model_missing",
            "ollama": "running",
            "minicpm_v_available": has_minicpm,
            "models": [m.get("name") for m in models],
        }
    except Exception as exc:
        return {"status": "unhealthy", "error": str(exc)}


@app.post("/extract/nic")
async def extract_nic(
    image: UploadFile = File(...),
    x_internal_secret: str | None = Header(default=None, alias="X-Internal-Secret"),
    x_side: str = Header(default="front", alias="X-Side"),
):
    _verify_secret(x_internal_secret)

    side = x_side.lower().strip()
    if side not in {"front", "back"}:
        raise HTTPException(status_code=400, detail="X-Side must be 'front' or 'back'")

    image_bytes = await image.read()
    if len(image_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")

    def _detect_format(raw: bytes) -> str:
        if raw.startswith(b"\x89PNG\r\n\x1a\n"):
            return "PNG"
        if raw.startswith(b"\xff\xd8\xff"):
            return "JPEG"
        if raw.startswith(b"RIFF") and b"WEBP" in raw[8:16]:
            return "WEBP"
        return ""

    try:
        # Validate image in memory only.
        with Image.open(BytesIO(image_bytes)) as img:
            img.verify()
            detected_format = (img.format or "").upper()
    except Exception as exc:
        detected_format = _detect_format(image_bytes)
        if not detected_format:
            raise HTTPException(status_code=400, detail=f"Invalid image: {exc}") from exc

    if image.content_type not in ALLOWED_MIME_TYPES:
        allowed_formats = {"JPEG", "JPG", "PNG", "WEBP"}
        if detected_format not in allowed_formats:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid file type {image.content_type}. "
                    f"Allowed: {sorted(ALLOWED_MIME_TYPES)}"
                ),
            )

    try:
        data = await _extract_with_ollama(image_bytes, side)
    except Exception as exc:
        logger.exception("Extraction failed side=%s: %s", side, exc)
        raise HTTPException(status_code=500, detail=f"Extraction failed: {exc}") from exc

    # Return the flat payload expected by backend and ops guides.
    return data
