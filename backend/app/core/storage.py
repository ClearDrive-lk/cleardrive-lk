# backend/app/core/storage.py

"""Supabase Storage helper used by KYC upload routes."""

from __future__ import annotations

from dataclasses import dataclass

import httpx
from app.core.config import settings


@dataclass
class StorageService:
    """Small async client for Supabase Storage uploads."""

    base_url: str
    api_key: str

    async def upload_file(
        self,
        *,
        bucket: str,
        file_path: str,
        file_content: bytes,
        content_type: str,
    ) -> dict[str, str]:
        """Upload a file to Supabase Storage and return URLs."""
        clean_base = self.base_url.rstrip("/")
        object_path = f"{bucket}/{file_path.lstrip('/')}"
        upload_url = f"{clean_base}/storage/v1/object/{object_path}"
        public_url = f"{clean_base}/storage/v1/object/public/{object_path}"

        headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": content_type,
            "x-upsert": "true",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(upload_url, headers=headers, content=file_content)
            response.raise_for_status()

        return {
            "path": object_path,
            "url": public_url,
        }


storage = StorageService(
    base_url=settings.SUPABASE_URL,
    api_key=settings.SUPABASE_KEY,
)
