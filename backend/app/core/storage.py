# backend/app/core/storage.py

"""
Supabase Storage client for file uploads.
"""

from typing import TYPE_CHECKING, Any

from app.core.config import settings

if TYPE_CHECKING:
    from supabase import Client


class SupabaseStorageClient:
    """Supabase Storage wrapper."""

    def __init__(self):
        self._client: "Client | None" = None

    @property
    def client(self) -> "Client":
        if self._client is None:
            from supabase import create_client

            self._client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        return self._client

    async def upload_file(
        self,
        bucket: str,
        file_path: str,
        file_content: bytes,
        content_type: str,
    ) -> dict[str, Any]:
        """
        Upload a file to Supabase Storage.

        Args:
            bucket:       Storage bucket name (e.g. "kyc-documents")
            file_path:    Path inside the bucket (e.g. "{user_id}/nic_front.jpg")
            file_content: Raw file bytes
            content_type: MIME type (e.g. "image/jpeg")

        Returns:
            {"path": str, "url": str}

        Raises:
            Exception: on Supabase upload failure
        """
        response = self.client.storage.from_(bucket).upload(
            path=file_path,
            file=file_content,
            # Allow safe retries when the same file path already exists.
            file_options={"content-type": content_type, "upsert": "true"},
        )

        # supabase-py raises on error, but guard anyway
        if hasattr(response, "error") and response.error:
            raise Exception(f"Supabase upload error: {response.error}")

        public_url = self.client.storage.from_(bucket).get_public_url(file_path)

        return {
            "path": file_path,
            "url": public_url,
        }

    async def delete_file(self, bucket: str, file_path: str) -> None:
        """Delete a file from Supabase Storage."""
        response = self.client.storage.from_(bucket).remove([file_path])

        if hasattr(response, "error") and response.error:
            raise Exception(f"Supabase delete error: {response.error}")

    def get_public_url(self, bucket: str, file_path: str) -> str:
        """Get the public URL for an existing file."""
        return self.client.storage.from_(bucket).get_public_url(file_path)


# Singleton — imported as `from app.core.storage import storage`
storage = SupabaseStorageClient()
