# backend/app/core/storage.py

"""
Supabase Storage client for file uploads.
Author: Pavara (Malith should have created this)
Story: CD-50
"""

import os
from typing import Any, Dict

try:
    from supabase import Client, create_client
except ModuleNotFoundError:  # pragma: no cover - optional dependency in some CI jobs
    Client = Any  # type: ignore[misc,assignment]
    create_client = None


class SupabaseStorage:
    """Supabase Storage client wrapper."""

    def __init__(self):
        """Initialize storage wrapper without connecting immediately."""
        self.client: Client | None = None

    def _ensure_client(self) -> Client:
        """Create Supabase client lazily to avoid import-time failures in tests."""
        if self.client is not None:
            return self.client

        if create_client is None:
            raise RuntimeError("Supabase dependency is not installed")

        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            raise RuntimeError(
                "Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_KEY in .env"
            )

        self.client = create_client(supabase_url, supabase_key)
        return self.client

    async def upload_file(
        self,
        bucket: str,
        file_path: str,
        file_content: bytes,
        content_type: str = "application/octet-stream",
    ) -> Dict:
        """
        Upload file to Supabase Storage.

        Args:
            bucket: Bucket name (e.g., "kyc-documents")
            file_path: Path within bucket (e.g., "user_id/nic_front.jpg")
            file_content: File bytes
            content_type: MIME type (e.g., "image/jpeg")

        Returns:
            {"url": "https://...", "path": "..."}
        """

        try:
            client = self._ensure_client()

            # Upload to Supabase Storage
            client.storage.from_(bucket).upload(
                path=file_path, file=file_content, file_options={"content-type": content_type}
            )

            # Get public URL
            public_url = client.storage.from_(bucket).get_public_url(file_path)

            return {"url": public_url, "path": file_path}

        except Exception as e:
            raise Exception(f"Supabase upload failed: {str(e)}")

    async def download_file(self, bucket: str, file_path: str) -> bytes:
        """Download file from Supabase Storage."""
        try:
            response = self._ensure_client().storage.from_(bucket).download(file_path)
            return response
        except Exception as e:
            raise Exception(f"Supabase download failed: {str(e)}")

    async def delete_file(self, bucket: str, file_path: str) -> bool:
        """Delete file from Supabase Storage."""
        try:
            self._ensure_client().storage.from_(bucket).remove([file_path])
            return True
        except Exception as e:
            raise Exception(f"Supabase delete failed: {str(e)}")


# Global instance
storage = SupabaseStorage()
