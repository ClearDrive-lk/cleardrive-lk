# backend/app/modules/shipping/document_validator.py
from __future__ import annotations

from typing import Tuple
from fastapi import UploadFile

try:
    import magic  # python-magic (or python-magic-bin on Windows)
except ImportError as e:
    magic = None


class DocumentValidator:
    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "image/jpeg",
        "image/png",
    }

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    @staticmethod
    async def read_bytes(file: UploadFile) -> bytes:
        content = await file.read()
        await file.seek(0)  # important: reset for later usage (upload/hash/etc.)
        return content

    @staticmethod
    async def validate_mime_and_size(file: UploadFile) -> Tuple[str, int]:
        """
        Returns: (mime_type, file_size)
        Raises: ValueError with user-friendly message
        """
        content = await DocumentValidator.read_bytes(file)
        size = len(content)

        if size == 0:
            raise ValueError("File is empty")
        if size > DocumentValidator.MAX_FILE_SIZE:
            raise ValueError("File too large. Maximum size is 10MB")

        if magic is None:
            raise ValueError("MIME detection library not installed (python-magic)")

        detected = magic.from_buffer(content, mime=True)

        # Some systems may return image/jpg; normalize it
        if detected == "image/jpg":
            detected = "image/jpeg"

        if detected not in DocumentValidator.ALLOWED_MIME_TYPES:
            raise ValueError(
                f"Invalid file type. Allowed: PDF, JPG, PNG. Detected: {detected}"
            )

        return detected, size
